import gc
import os

import pytest


def _register_mesa_dll_dir() -> None:
    """Make Mesa3D's DLLs (opengl32.dll...) loadable on Windows CI.

    Must run *before* pyglet is imported, otherwise `opengl32.dll` may already
    be bound to the inbox GDI generic OpenGL 1.1 driver.
    """
    if os.name != "nt":
        return
    mesa_dir = os.getenv("MESA_DLL_DIR")
    if not mesa_dir or not os.path.isdir(mesa_dir):
        return
    try:
        os.add_dll_directory(mesa_dir)  # type: ignore[attr-defined]  # Windows-only API
    except (OSError, AttributeError): # pragma: no cover - defensive
        pass
    # Belt and braces: Mesa honors these even when a driver was auto-selected.
    os.environ.setdefault("GALLIUM_DRIVER", "llvmpipe")
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")


_register_mesa_dll_dir()


def _force_legacy_windows_font_renderer() -> None:
    """Rasterise text with GDI+ instead of DirectWrite on Windows.

    Pyglet lays text out through Direct2D by default on Windows, which needs a
    D3D device to draw a glyph into a WIC bitmap. On a CI runner there is no
    usable GPU, so that creation fails with:

        OSError: [WinError -2003238904] An internal error (Direct2D bug) occurred

    The failure is raised inside the ctypes callback pyglet renders glyphs from,
    which swallows it. The text layout is then left with a non-empty owner run
    and an *empty* glyph list, so the next line runs off the end:

        pyglet/text/layout/base.py:1647: owner = glyphs[start].owner
        IndexError: list index out of range

    In other words `arcade.Text(...).draw()` explodes from deep inside pyglet on
    a runner that has a perfectly usable OpenGL context (Mesa llvmpipe, see
    `_register_mesa_dll_dir`). That is an infrastructure limitation, not a defect
    in the drawing code the tests are actually there to check.

    `win32_gdi_font` selects the legacy GDI+ renderer, which needs no D3D
    device. It is only read on pyglet's win32/cygwin branch, hence the guard.
    Like the DLL directory above, it has to be set before `pyglet.font` is
    imported: that module resolves its font class once, at import time.
    """
    if os.name != "nt":
        return
    import pyglet

    pyglet.options["win32_gdi_font"] = True


_force_legacy_windows_font_renderer()

import arcade  # noqa: E402  (must be imported after the DLL directory setup)
import arcade.window_commands as window_commands  # noqa: E402


# --- OpenGL availability -------------------------------------------------
# Arcade/Pyglet need a *real* OpenGL context (>= 3.3 core) to build a window.
# CI runners on Windows only expose the GDI generic OpenGL 1.1 driver (no
# WGL_ARB_pixel_format), which makes `arcade.Window(...)` raise. Rather than
# turning the whole suite red for an infrastructure reason, we detect the
# failure once and turn it into a skip.
_GLX_MESSAGES = (
    "opengl",
    "wgl",
    "glx",
    "gl_exception",
    "missingfunctionexception",
    "no gl context",
    "invalid operation",
    # No display server at all (headless Linux without Xvfb, no window station):
    # same infrastructure problem as a missing GL driver.
    "nosuchdisplayexception",
    "cannot connect to",
)

_gl_failure_reason: "str | None" = None


def _looks_like_gl_failure(exc: BaseException) -> bool:
    """True if `exc` is a "this machine has no usable OpenGL" error."""
    if type(exc).__name__ in ("GLException", "MissingFunctionException"):
        return True
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in _GLX_MESSAGES)


def _gl_unavailable_reason() -> "str | None":
    """Reason recorded after the first failed window creation, else None.

    Exposed for debugging: `pytest -rs` shows the skip reason, and this helper
    lets a test assert that GL was (or was not) available.
    """
    return _gl_failure_reason


_original_window_init = arcade.Window.__init__


def _window_init_with_gl_guard(self, *args, **kwargs): # noqa: ANN001, ANN202
    """`arcade.Window.__init__` that skips the test when OpenGL is missing."""
    global _gl_failure_reason

    if _gl_failure_reason is not None:
        pytest.skip(_gl_failure_reason)

    try:
        _original_window_init(self, *args, **kwargs)
    except Exception as exc: # noqa: BLE001 - re-raised unless it is a GL issue
        if not _looks_like_gl_failure(exc):
            raise
        _gl_failure_reason = (
            "Contexte OpenGL indisponible sur cette plateforme "
            f"({type(exc).__name__}: {exc}). Test ignoré."
        )
        pytest.skip(_gl_failure_reason)


arcade.Window.__init__ = _window_init_with_gl_guard


class _HeadlessWindow:
    """Minimal stub that satisfies `arcade.Window` API used in tests."""

    def __init__(self):
        self.ctx = None
        self.width = 1
        self.height = 1
        self.visible = False

    def close(self):
        pass


def _ensure_headless_arcade_window() -> None:
    """Ensure an arcade Window handle exists even in headless runs."""
    try:
        window_commands.get_window()
    except RuntimeError:
        window_commands.set_window(_HeadlessWindow())


_ensure_headless_arcade_window()


# Top-level defensive replacement: if running in CI or DISABLE_SHADERS is set,
# replace ClosedPlayground at import time so test modules that import the class
# early will see the no-shader variant.
if os.getenv("GITHUB_ACTIONS", "") == "true" or os.getenv("DISABLE_SHADERS", "") == "1":
    try:
        import swarm_rescue.simulation.gui_map.closed_playground as closed_playground_module
        original_cls = getattr(closed_playground_module, "ClosedPlayground", None)
        if original_cls is not None:
            class ClosedPlaygroundNoShader(original_cls):
                def __init__(self, *args, **kwargs):
                    kwargs["use_shaders"] = False
                    super().__init__(*args, **kwargs)

            closed_playground_module.ClosedPlayground = ClosedPlaygroundNoShader
    except Exception:
        # Best-effort: don't fail import of conftest
        pass


def pytest_runtest_setup():
    """Pytest hook to provision a headless window before each test case."""
    _ensure_headless_arcade_window()


def pytest_runtest_teardown():
    """Ensure headless window is ready in case a test closed it."""
    _ensure_headless_arcade_window()
    gc.collect()


# Autouse fixture (backup): if DISABLE_SHADERS=1 in the environment, ensure
# ClosedPlayground ignores shaders
@pytest.fixture(autouse=True)
def _force_disable_shaders_if_requested(monkeypatch):
    """If DISABLE_SHADERS=1 in the environment, ensure ClosedPlayground ignores shaders.

    This is non-invasive: it subclasses the real ClosedPlayground and forces
    use_shaders=False in its constructor, then monkeypatches the symbol in the
    module so tests that import ClosedPlayground get the no-shader variant.
    """
    if os.getenv("DISABLE_SHADERS", "") != "1" and os.getenv("GITHUB_ACTIONS", "") != "true":
        # nothing to do
        yield
        return

    try:
        # Import the module and original class
        import swarm_rescue.simulation.gui_map.closed_playground as closed_playground_module
        original_cls = getattr(closed_playground_module, "ClosedPlayground", None)
        if original_cls is None:
            yield
            return

        class ClosedPlaygroundNoShader(original_cls):
            def __init__(self, *args, **kwargs):
                # Force shaders off regardless of caller's intent
                kwargs["use_shaders"] = False
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(closed_playground_module, "ClosedPlayground",
                            ClosedPlaygroundNoShader)
    except Exception:
        # If anything goes wrong, avoid breaking tests: let them run as-is
        pass
    yield
