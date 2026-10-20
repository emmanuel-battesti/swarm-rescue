"""
Tests for the GL state Playground must not hijack.

`Playground` used to force `blend_func = (ONE, ZERO)` on the window context,
i.e. "overwrite the destination completely". That is global state which was
never restored, so alpha blending stayed disabled for the whole life of the
window. These tests lock in that the playground leaves the blend state alone.
"""

import pathlib
import sys

import pytest
import arcade
import arcade.window_commands as window_commands

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


@pytest.fixture
def playground():
    """A minimal playground, closed on teardown."""
    try:
        window_commands.get_window()
    except RuntimeError:
        arcade.Window(width=1, height=1, visible=False)
    pg = ClosedPlayground(size=(400, 300))
    try:
        yield pg
    finally:
        pg.close_window()


class TestBlendStateIsNotHijacked:
    """Playground must leave the global blend state to arcade."""

    def test_blend_func_is_arcade_default(self, playground):
        """Creating a playground must not disable alpha blending.

        Regression test: the playground used to set (ONE, ZERO), which stayed in
        effect for the whole lifetime of the window.
        """
        ctx = playground.ctx
        assert tuple(ctx.blend_func) == (ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA)

    def test_blend_func_is_not_overwrite_mode(self, playground):
        """The blend state must not be the destructive (ONE, ZERO) mode."""
        ctx = playground.ctx
        assert ctx.ZERO not in tuple(ctx.blend_func)

    def test_alpha_blending_is_still_available(self, playground):
        """A caller can enable alpha blending without the playground fighting it."""
        ctx = playground.ctx
        ctx.blend_func = (ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA)
        # Creating another playground must not silently change it back.
        other = ClosedPlayground(size=(400, 300))
        try:
            assert tuple(other.ctx.blend_func) == (ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA)
        finally:
            other.close_window()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
