"""
Tests for the view registry in `Playground`.

`Playground` keeps a list of views and pushes every entity to each of them
(`_add_to_views` / `_remove_from_views`). `add_view()` registers a view and
then populates it with the entities that already exist.

The registration has to happen *before* the population: populating calls
back into the view, and if that ever added an entity to the playground,
`_add_to_views` would skip a view that is not listed yet, and the entity
would silently never be drawn.
"""

import pathlib
import sys

import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.normal_wall import ColorWall
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


@pytest.fixture
def playground():
    pg = ClosedPlayground(size=(1200, 800))
    try:
        yield pg
    finally:
        pg.close_window()


def _add_wall(pg, pos_start, pos_end):
    wall = ColorWall(pos_start=pos_start, pos_end=pos_end, color=(200, 0, 0))
    pg.add(wall, initial_coordinates=wall.wall_coordinates)
    return wall


class RecordingView:
    """A minimal view that only records what it is asked to draw."""

    def __init__(self, on_add=None):
        self.sprites = []
        self._on_add = on_add

    def add_as_sprite(self, entity):
        self.sprites.append(entity)
        if self._on_add is not None:
            self._on_add()

    def remove_as_sprite(self, entity):
        self.sprites.remove(entity)


class TestWindowInjection:
    """
    The playground can be handed a window instead of creating one.

    This matters for ownership: whoever creates a window is responsible for
    closing it. Before, `Playground` always created its own, so a caller that
    wanted to draw into a window it controlled had no way in.
    """

    def test_an_injected_window_is_used(self):
        import arcade

        window = arcade.Window(width=320, height=240, visible=False)
        try:
            pg = ClosedPlayground(size=(400, 300), window=window)
            try:
                assert pg.window is window
                assert pg.ctx is window.ctx
            finally:
                pg.close_window()
        finally:
            window.close()

    def test_an_injected_window_is_not_closed_by_the_playground(self):
        """
        The playground did not create it, so it must not destroy it.

        Closing someone else's window is the kind of bug that only shows up in
        the test that runs after the one that needed it.
        """
        import arcade

        window = arcade.Window(width=320, height=240, visible=False)
        try:
            pg = ClosedPlayground(size=(400, 300), window=window)
            pg.close_window()

            # Still usable: the window outlived the playground.
            assert window.ctx is not None
            window.set_size(321, 241)
            # And the playground kept its reference rather than dropping it,
            # so `window` stays readable.
            assert pg.window is window
        finally:
            window.close()

    def test_an_owned_window_is_still_closed(self):
        """
        The default must keep behaving as before, or every existing caller
        would start leaking windows.
        """
        pg = ClosedPlayground(size=(400, 300))
        window = pg.window
        assert window is not None

        pg.close_window()

        assert pg.window is None


class TestViewRegistry:
    """Views must be registered once and kept in sync with the entities."""

    def test_view_is_registered_once(self, playground):
        """add_view() must not register the same view twice."""
        view = RecordingView()
        playground.add_view(view)

        assert playground._views.count(view) == 1

    def test_existing_entities_are_pushed_to_a_new_view(self, playground):
        """A view added later must receive the entities already present."""
        before = list(playground.elements)
        assert before, "the playground should start with its border walls"

        view = RecordingView()
        playground.add_view(view)

        assert all(entity in view.sprites for entity in before)

    def test_entity_added_after_the_view_reaches_it(self, playground):
        """An entity added afterward must be pushed to the registered views."""
        view = RecordingView()
        playground.add_view(view)

        wall = _add_wall(playground, (100, 100), (200, 100))

        assert wall in view.sprites

    def test_removed_entity_is_dropped_from_the_view(self, playground):
        """A removed entity must be dropped from the registered views."""
        view = RecordingView()
        playground.add_view(view)

        wall = _add_wall(playground, (100, 100), (200, 100))
        assert wall in view.sprites

        playground.remove(wall, definitive=True)

        assert wall not in view.sprites

    def test_entity_added_while_the_view_is_being_populated_is_drawn(self, playground, tmp_path):
        """An entity added *during* add_view() must still reach that view.

        This is the re-entrancy case the registration order protects. The
        callback fires the first time the view is populated, i.e. while
        add_view() is still running.
        """
        added = []

        def add_during_population():
            # Only trigger once, otherwise this recurses.
            if added:
                return
            added.append(True)
            _add_wall(playground, (300, 300), (400, 300))

        view = RecordingView(on_add=add_during_population)
        playground.add_view(view)

        assert added, "the callback should have fired"
        late = [e for e in playground.elements if isinstance(e, ColorWall)]
        assert late, "the late wall should be in the playground"
        assert all(entity in view.sprites for entity in late), (
            "an entity added while the view was being populated was not drawn"
        )
