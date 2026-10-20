"""
Architecture test: the model must not depend on the presentation.

The simulator is split in two layers:

- the **model** (`drone`, `elements`, `ray_sensors`, `utils`, and the top-level
  `collision_handlers`): physics, entities, sensors. It must be usable, and
  testable, without any window.
- the **presentation** (`gui_map`): arcade window, views, framebuffers, and the
  `Playground` that ties them together.

An import from the model into `gui_map` is not a style question, it is a design
one. The lidar is the proof: `RayCompute` used to reach into the view, draw into
its framebuffer and read the pixels back, which is why a window resize could
break the physics (see the resize bug and its regression test in
`tests/test_window_resize.py`). Every `model -> gui_map` import is an
opportunity for the same accident.

`TYPE_CHECKING` imports are allowed: they are erased at runtime, cost nothing,
and are the right tool for annotations.

This test exists because the fix is worthless without it: without a guard the
violations come back with the next contribution.
"""

import ast
import pathlib
import sys

# Insert the 'src' and 'examples' directories into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"

PRESENTATION_PACKAGE = "gui_map"

# The packages that make up the model: everything that must stay free of any
# rendering concern.
MODEL_PACKAGES = (
    "drone",
    "elements",
    "ray_sensors",
    "utils",
)


def _model_files():
    """Yield every module file that belongs to the model layer."""
    simulation = SRC_DIR / "swarm_rescue" / "simulation"
    for package in MODEL_PACKAGES:
        for path in sorted((simulation / package).rglob("*.py")):
            yield path
    # Top-level model modules that sit directly under `simulation/`.
    for path in sorted(simulation.glob("*.py")):
        yield path


def _gui_map_import_names(node, path: pathlib.Path):
    """Yield (lineno, module) for the gui_map imports carried by `node`."""
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        # Absolute import of the presentation package.
        if f".{PRESENTATION_PACKAGE}." in f".{module}.":
            return [(node.lineno, module)]
        # Relative import (`from .gui_map import x` inside a model package).
        if node.level and f"{PRESENTATION_PACKAGE}." in f"{module}.":
            return [(node.lineno, module)]
    return []


def _runtime_gui_map_imports(path: pathlib.Path):
    """
    Return the runtime imports of `gui_map` found in `path`.

    Imports nested inside an `if TYPE_CHECKING:` block are ignored: they are
    erased before the module is executed, so they cannot create a runtime
    dependency on the presentation.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_If(self, node):
            test = node.test
            is_type_checking = isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"
            is_future = (
                isinstance(test, ast.ImportFrom) and test.module == "__future__"
            )
            if is_type_checking or is_future:
                # Report what is inside the guard, but let the caller know it
                # is type-only by tagging the line number as None.
                for statement in node.body:
                    for child in ast.walk(statement):
                        for lineno, module in _gui_map_import_names(child, path):
                            found.append((None, module))
                return
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            found.extend(_gui_map_import_names(node, path))

        def visit_Import(self, node):
            for alias in node.names:
                if f".{PRESENTATION_PACKAGE}." in f".{alias.name}.":
                    found.append((node.lineno, alias.name))

    Visitor().visit(tree)
    # A `None` line number marks a type-only import: drop it, it is allowed.
    return [(lineno, module) for lineno, module in found if lineno is not None]


def test_model_never_imports_the_presentation():
    """No model module may import `gui_map` at runtime."""
    violations = []

    for path in _model_files():
        for lineno, module in _runtime_gui_map_imports(path):
            relative = path.relative_to(SRC_DIR)
            violations.append(
                f"{relative}:{lineno} imports {PRESENTATION_PACKAGE}.{module}"
            )

    assert not violations, (
        "The model must not depend on the presentation layer.\n"
        "These imports let the physics reach into the rendering, which is how a "
        "window resize once broke the lidar:\n  "
        + "\n  ".join(violations)
        + "\nMove the shared code out of gui_map/, or import it under TYPE_CHECKING "
        "if it is only used to annotate a variable."
    )


def test_the_architecture_test_would_catch_a_violation():
    """
    Guard the guard.

    A test that cannot fail is worse than no test: it gives the false
    impression that the boundary is enforced. This feeds the checker a module
    that does exactly what the rule forbids, and checks that it is reported.
    """
    sample = "from swarm_rescue.simulation.gui_map.playground import Playground\n"
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_ImportFrom(self, node):
            found.extend(_gui_map_import_names(node, pathlib.Path("offender.py")))

    Visitor().visit(ast.parse(sample, filename="offender.py"))

    assert found, "the checker missed a plain runtime import of gui_map"


def test_the_architecture_test_allows_type_checking():
    """A `TYPE_CHECKING` import is erased at runtime and must stay allowed."""
    sample = (
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from swarm_rescue.simulation.gui_map.playground import Playground\n"
    )
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_If(self, node):
            if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                return
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            found.extend(_gui_map_import_names(node, pathlib.Path("innocent.py")))

    Visitor().visit(ast.parse(sample, filename="innocent.py"))

    assert not found, "a TYPE_CHECKING import must not be reported as a violation"


def test_matplotlib_stays_off_the_import_path():
    """
    Importing the simulator must not drag matplotlib in.

    `matplotlib.pyplot` costs roughly half a second to import and is used only
    by two debugging helpers and the PDF report. A module-level import meant
    every participant, every test and every evaluation paid for it.

    This is checked in a subprocess because by the time pytest runs, other
    tests have imported matplotlib for real; an in-process check would only
    ever see the pollution.
    """
    import subprocess
    import sys

    probe = (
        "import sys\n"
        "import swarm_rescue.simulation.gui_map.closed_playground\n"
        "import swarm_rescue.simulation.reporting.evaluation_pdf_report\n"
        "assert 'matplotlib' not in sys.modules, 'matplotlib was imported'\n"
        "assert 'pymunk.matplotlib_util' not in sys.modules\n"
        "print('clean')\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(SRC_DIR.parents[1]),
    )

    assert result.returncode == 0, (
        "importing the simulator pulled matplotlib back in:\n"
        f"{result.stderr}"
    )
