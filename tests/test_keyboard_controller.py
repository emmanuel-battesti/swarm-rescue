"""
Tests for the keyboard controller.

The arrow keys drive two different commands depending on the Shift modifier:
the plain key turns the drone, Shift + key strafes it. These tests lock in
that switching the modifier while the key is held switches mode cleanly, and
that the other commands are left untouched.
"""

import pathlib
import sys

import pytest
import arcade

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.keyboard_controller import KeyboardController

NO_MODIFIER = 0
SHIFT = arcade.key.MOD_SHIFT


@pytest.fixture
def controller():
    return KeyboardController()


class TestRotationAndLateral:
    """The LEFT/RIGHT keys drive either rotation or lateral movement."""

    @pytest.mark.parametrize("key,expected", [(arcade.key.LEFT, 1.0), (arcade.key.RIGHT, -1.0)])
    def test_plain_key_turns(self, controller, key, expected):
        """Without Shift the key commands a rotation."""
        controller.on_key_press(key, NO_MODIFIER)
        assert controller.control()["rotation"] == expected
        assert controller.control()["lateral"] == 0.0

    @pytest.mark.parametrize("key,expected", [(arcade.key.LEFT, 1.0), (arcade.key.RIGHT, -1.0)])
    def test_shift_key_strafes(self, controller, key, expected):
        """With Shift the same key commands a lateral movement."""
        controller.on_key_press(key, SHIFT)
        assert controller.control()["lateral"] == expected
        assert controller.control()["rotation"] == 0.0

    @pytest.mark.parametrize("key", [arcade.key.LEFT, arcade.key.RIGHT])
    def test_releasing_shift_switches_back_to_turning(self, controller, key):
        """Releasing Shift while the key is held must stop the lateral move.

        Regression test: the lateral command used to stay at its value, so the
        drone kept strafing *and* turning at the same time.
        """
        controller.on_key_press(key, SHIFT)
        assert controller.control()["lateral"] != 0.0

        # Shift is released, but the arrow key is still held down.
        controller.on_key_press(key, NO_MODIFIER)

        assert controller.control()["lateral"] == 0.0
        assert controller.control()["rotation"] != 0.0

    @pytest.mark.parametrize("key", [arcade.key.LEFT, arcade.key.RIGHT])
    def test_pressing_shift_switches_to_strafing(self, controller, key):
        """Pressing Shift while the key is held must stop the rotation.

        Mirror case of the previous test.
        """
        controller.on_key_press(key, NO_MODIFIER)
        assert controller.control()["rotation"] != 0.0

        controller.on_key_press(key, SHIFT)

        assert controller.control()["rotation"] == 0.0
        assert controller.control()["lateral"] != 0.0

    @pytest.mark.parametrize("key", [arcade.key.LEFT, arcade.key.RIGHT])
    def test_release_clears_both_commands(self, controller, key):
        """Releasing the key stops both the rotation and the lateral move."""
        controller.on_key_press(key, SHIFT)
        controller.on_key_release(key, NO_MODIFIER)
        assert controller.control()["lateral"] == 0
        assert controller.control()["rotation"] == 0

    def test_modifier_changes_do_not_affect_other_commands(self, controller):
        """Switching the Shift modifier must not disturb the other commands."""
        controller.on_key_press(arcade.key.UP, NO_MODIFIER)
        controller.on_key_press(arcade.key.W, NO_MODIFIER)

        controller.on_key_press(arcade.key.LEFT, SHIFT)
        assert controller.control()["forward"] == 1.0
        assert controller.control()["grasper"] == 1

        controller.on_key_press(arcade.key.LEFT, NO_MODIFIER)
        assert controller.control()["forward"] == 1.0
        assert controller.control()["grasper"] == 1

    def test_unrelated_key_does_not_clear_movement(self, controller):
        """Pressing an unrelated key must not stop the ongoing movement."""
        controller.on_key_press(arcade.key.LEFT, NO_MODIFIER)
        controller.on_key_press(arcade.key.UP, NO_MODIFIER)

        assert controller.control()["rotation"] == 1.0
        assert controller.control()["forward"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
