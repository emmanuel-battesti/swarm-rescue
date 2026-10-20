"""
The participant API is a contract, so it is written down and checked.

A solution only ever needs `control()` plus a handful of sensor accessors.
Everything else a drone exposes -- `pre_step`, `collide_wall`, `draw_gps`, the
draw_* family -- is framework plumbing with no leading underscore, because the
simulator calls it on every drone it holds.

The convention alone therefore says nothing about what is supported. These
tests pin the difference down.
"""

import ast
import pathlib
import sys

# Insert the 'src' and 'examples' directories into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.drone_abstract import (
    PARTICIPANT_API,
    DroneAbstract,
)
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


class _ProbeDrone(DroneAbstract):
    """A drone that does nothing, used only to inspect the object."""

    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


def _resolve_on_a_live_drone(names):
    """Return the names that are neither on the class nor on a real instance."""
    playground = ClosedPlayground(size=(400, 300))
    try:
        drone = _ProbeDrone(playground)
        return sorted(
            name
            for name in names
            if not hasattr(DroneAbstract, name) and not hasattr(drone, name)
        )
    finally:
        playground.close_window()


def test_the_participant_api_is_not_empty():
    """A guard against an accidental wipe of the whole list."""
    assert len(PARTICIPANT_API) > 20


def test_every_listed_member_exists():
    """Each name must resolve on the class or on one of its bases."""
    on_the_class = {
        name
        for name in PARTICIPANT_API
        if hasattr(DroneAbstract, name) or hasattr(Agent, name)
        or hasattr(Entity, name)
    }
    # The rest are instance attributes assigned in __init__ (`identifier`,
    # `grasper`, ...), which a class-level check cannot see.
    missing = _resolve_on_a_live_drone(PARTICIPANT_API - on_the_class)
    assert not missing, (
        "PARTICIPANT_API lists members that do not exist: "
        + ", ".join(missing)
        + ". Either the member was renamed, or the list was left stale."
    )


def test_no_listed_member_is_private():
    """
    A private name in the contract would be a contradiction.

    If something starts with an underscore, the framework is telling us it is
    not part of the API, so it must not be advertised as one.
    """
    private = sorted(name for name in PARTICIPANT_API if name.startswith("_"))
    assert not private, "PARTICIPANT_API must not contain private names: " + ", ".join(private)


def test_control_and_define_message_are_in_the_contract():
    """
    These two are the only methods a participant must implement.

    If they ever leave the list, the example solutions and the README stop
    describing the same thing the simulator does.
    """
    assert "control" in PARTICIPANT_API
    assert "define_message_for_all" in PARTICIPANT_API


def test_true_state_is_not_silent_about_being_a_special_case():
    """
    `true_position()` and friends stay reachable but are not in the contract.

    They are the ground truth: using them inside a controller is cheating, and
    `true_state_guard` raises when it happens. They must not be advertised as
    a normal sensor, which is why they are absent from PARTICIPANT_API.
    """
    assert hasattr(DroneAbstract, "true_position"), "the guard needs the method to exist"
    assert "true_position" not in PARTICIPANT_API


def test_the_disabled_properties_are_not_advertised_as_api():
    """
    `position`, `angle`, `velocity` and `angular_velocity` exist only to raise.

    They are traps pointing at the measured_* accessors, so listing them in
    PARTICIPANT_API would advertise as supported exactly what a controller must
    not use.
    """
    traps = {"position", "angle", "velocity", "angular_velocity"}
    advertised = sorted(traps & PARTICIPANT_API)
    assert not advertised, (
        "PARTICIPANT_API advertises disabled trap properties: "
        + ", ".join(advertised)
    )


def test_the_contract_is_much_smaller_than_the_class():
    """
    Quantify what the contract buys.

    If the gap ever closes, either the plumbing grew names that should have
    been private, or the boundary is no longer worth drawing.
    """
    internal = {name for name in dir(DroneAbstract) if not name.startswith("_")}
    plumbing = internal - PARTICIPANT_API
    assert plumbing, "expected DroneAbstract to expose more than the participant API"
    assert len(PARTICIPANT_API) < len(internal) / 2, (
        "the participant API no longer looks like a small subset of the class: "
        f"{len(PARTICIPANT_API)} contract members vs {len(internal)} public ones"
    )


SOLUTION_DIRS = (
    pathlib.Path(__file__).resolve().parent.parent / "examples",
    pathlib.Path(__file__).resolve().parent.parent / "src" / "swarm_rescue" / "solutions",
)


def _drone_classes_on_disk():
    """Yield (path, class node) for every drone subclass shipped with the project."""
    for directory in SOLUTION_DIRS:
        for path in sorted(directory.rglob("*.py")):
            # `encoding="utf-8"` is not optional here: without it `read_text()`
            # decodes with the *locale* encoding, and the Windows runner's is
            # cp1252. The examples are valid UTF-8, but
            # exemple_03_fixed_ratio_match_window.py contains a byte cp1252
            # cannot decode at all, which aborted this walk on Windows before it
            # had checked a single solution. Pinning the encoding states what
            # these files are and stops it depending on where the tests run.
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if any("Drone" in ast.unparse(base) for base in node.bases):
                    yield path, node


def test_the_shipped_solutions_stay_inside_the_contract():
    """
    The examples are the documentation a participant copies from.

    So they are the first thing that must not start relying on internal
    plumbing: if one of them calls something outside PARTICIPANT_API, either
    the API is missing a member every solution needs (and it belongs in the
    contract), or the example has started using something private.

    Only the two methods a participant writes are checked; a helper the
    example defines for itself is none of our business.
    """
    # Everything a drone already has, public or not: if a controller touches
    # one of these and it is not in the contract, that is what we want to see.
    # Instance-only attributes are not in `dir()`, so the contract entries for
    # them (`identifier`, `grasper`, ...) are never flagged anyway.
    drone_surface = set(dir(DroneAbstract)) | set(dir(Agent)) | set(dir(Entity))

    offenders = []

    for path, class_node in _drone_classes_on_disk():
        for method in class_node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            if method.name not in ("control", "define_message_for_all"):
                continue

            used = {
                node.attr
                for node in ast.walk(method)
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
            }
            outside = sorted(
                name
                for name in used
                if name in drone_surface and name not in PARTICIPANT_API
            )
            if outside:
                offenders.append(
                    f"{path.name}:{method.lineno} {class_node.name}."
                    f"{method.name}() uses {', '.join(outside)}"
                )

    assert not offenders, (
        "The shipped solutions reach outside the participant API:\n  "
        + "\n  ".join(offenders)
        + "\nEither promote the member to PARTICIPANT_API, or stop using it."
    )
