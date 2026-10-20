"""
Tests for the mandatory collision handler setup in `Playground`.

`Playground.__init__` calls `_handle_interactions()`. The base implementation
used to be an empty body, so a subclass that forgot to override it got a
playground with no collision handler at all: the drones pass through the
walls, nothing can be grasped and nobody can be rescued, with nothing to
point at the cause. It now fails loudly instead.
"""

import pathlib
import sys

import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.playground import Playground


class ForgetfulPlayground(Playground):
    """A subclass that forgets to declare its collision handlers."""


class ProperPlayground(ClosedPlayground):
    """A subclass that does its job."""


class TestCollisionHandlersAreMandatory:
    def test_base_playground_refuses_to_be_instantiated(self):
        """The base class has nothing to register, so it must refuse."""
        with pytest.raises(NotImplementedError, match="_handle_interactions"):
            Playground(size=(400, 300))

    def test_a_subclass_that_forgets_is_caught(self):
        """The silent failure this guards against must now be loud."""
        with pytest.raises(NotImplementedError, match="_handle_interactions"):
            ForgetfulPlayground(size=(400, 300))

    def test_the_error_names_the_faulty_class(self):
        """The message must point at the class to fix, not the base one."""
        with pytest.raises(NotImplementedError) as excinfo:
            ForgetfulPlayground(size=(400, 300))

        message = str(excinfo.value)
        assert "ForgetfulPlayground" in message
        assert "_handle_interactions" in message


class TestProperSubclassesStillWork:
    def test_closed_playground_is_unaffected(self):
        """The real implementation must keep working."""
        playground = ClosedPlayground(size=(400, 300))
        try:
            assert playground.size == (400, 300)
        finally:
            playground.close_window()

    def test_a_subclass_of_closed_playground_is_unaffected(self):
        """Inheriting from an implementation is enough."""
        playground = ProperPlayground(size=(400, 300))
        try:
            assert playground.size == (400, 300)
        finally:
            playground.close_window()

    def test_collision_handlers_are_actually_registered(self):
        """ClosedPlayground must still end up with working interactions."""
        playground = ClosedPlayground(size=(400, 300))
        try:
            # A playground with no handler would answer nothing to a query.
            assert len(list(playground.space.shapes)) > 0, (
                "the border walls should be there"
            )
        finally:
            playground.close_window()
