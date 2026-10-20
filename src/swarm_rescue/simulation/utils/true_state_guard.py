"""
Guard against reading the ground truth from the participants' controllers.

The participants of the competition write the drone controllers, i.e.
``control()`` and ``define_message_for_all()``. They must reason from the
simulated sensors (GPS, compass, lidar, ...), which are noisy and can be
disabled, because that is the exercise.

The ``true_*`` accessors return the exact state of an entity. They stay
available for debugging, logging, drawing and for the evaluation itself, but
they raise ``TrueStateAccessError`` while participant code is running.

The guard is a single simulation-wide flag rather than one per object, so
that one context manager covers everything the controllers can reach: the
drones, the wounded persons they grasp, and anything added later. It is
scoped (restored in a ``finally`` block), so a controller raising does not
leave the ground truth locked for the rest of the run.

Outside ``control()`` and ``define_message_for_all()`` the guard is simply not
raised, so drawing and logging hooks can read the ground truth freely. See
``ALLOW_TRUE_STATE_ENV_VAR`` for deliberately turning the guard off.
"""

import os
from contextlib import contextmanager

# Set this environment variable to a truthy value ("1", "true", "yes") to let a
# participant's own code read `true_position()` and friends from inside
# `control()` and `define_message_for_all()`.
#
# Why this exists: a participant sometimes needs to check what their controller
# is really acting on -- comparing a commanded heading against the true one, or
# logging a trajectory -- and the alternative is to comment the guard out in the
# simulator, which is easy to forget to revert. An environment variable cannot
# be left switched on by accident in a committed file, and it cannot travel in a
# submission: `submission_guidelines.md` asks for the drone code only, and the
# evaluator runs their own copy of the simulator, so the variable is unset there
# and the guard applies again.
#
# The guard is ON by default. An evaluation run must never set it.
ALLOW_TRUE_STATE_ENV_VAR: str = "SWARM_RESCUE_ALLOW_TRUE_STATE"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def true_state_is_allowed() -> bool:
    """
    Whether the ground-truth guard has been deliberately disabled.

    Returns:
        bool: True when `ALLOW_TRUE_STATE_ENV_VAR` is set to a truthy value, in
            which case the `true_*` accessors work even inside `control()`.
    """
    return os.environ.get(ALLOW_TRUE_STATE_ENV_VAR, "").strip().lower() in _TRUTHY


class TrueStateAccessError(RuntimeError):
    """
    Raised when a ground-truth accessor is used from a participant's
    controller.

    The ``true_*`` accessors (true_position(), true_angle(), true_velocity())
    return the exact state of an entity, without the sensor noise the
    participants are supposed to cope with.
    """


# True while the participants' own code is running. Not a per-instance flag:
# a controller reaches several objects (its own drone, the wounded person it
# grasps), and they must all be protected at once.
_inside_participant_code = False


@contextmanager
def participant_code():
    """
    Mark the enclosed block as participants' controller code.

    While this block runs, the ground-truth accessors raise
    TrueStateAccessError instead of silently handing out the exact state.

    Yields:
        None.
    """
    global _inside_participant_code

    previous = _inside_participant_code
    _inside_participant_code = True
    try:
        yield
    finally:
        # Restored even if the controller raises, so one faulty drone cannot
        # lock the ground truth away for the rest of the run.
        _inside_participant_code = previous


def is_inside_participant_code() -> bool:
    """
    Whether the participants' code is currently running.

    Returns:
        bool: True inside a participant_code() block.
    """
    return _inside_participant_code


def check_true_state_access(name: str, alternative: str) -> None:
    """
    Refuse a ground-truth read while the participants' code is running.

    Args:
        name (str): The name of the accessor being called.
        alternative (str): What to use instead.

    Raises:
        TrueStateAccessError: If called from a controller, unless
            `ALLOW_TRUE_STATE_ENV_VAR` deliberately disables the guard.
    """
    if _inside_participant_code and not true_state_is_allowed():
        raise TrueStateAccessError(
            f"{name}() returns the exact state, without the sensor noise, so "
            f"it cannot be used to compute a command. Use {alternative} "
            f"instead."
        )
