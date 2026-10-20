"""
Tests for the `agents` / `elements` caches in `Playground`.

Those properties filter out the removed entities, and are read on every
simulation step, so the result is cached and invalidated through the
`_agents_cache_needs_update` / `_elements_cache_needs_update` flags.

These tests pin the invalidation: a stale cache would silently hide an
added or a removed entity from the whole simulation.

Note `ClosedPlayground` builds four border walls on creation, so the
collections are never empty; the assertions are relative to whatever the
playground starts with.
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


class TestCollectionsCache:
    """The cached lists must never go stale."""

    def test_element_is_visible_after_being_added(self, playground):
        """A newly added element must appear in `elements` right away."""
        # Prime the cache first, so the addition has to invalidate it.
        before = playground.elements
        assert len(before) > 0, "the playground should start with its border walls"

        wall = _add_wall(playground, (100, 100), (200, 100))

        assert wall in playground.elements
        assert len(playground.elements) == len(before) + 1

    def test_removed_element_disappears_from_elements(self, playground):
        """A removed element must not linger in `elements`."""
        wall = _add_wall(playground, (100, 100), (200, 100))
        assert wall in playground.elements

        playground.remove(wall, definitive=True)

        assert wall not in playground.elements

    def test_cache_is_actually_reused(self, playground):
        """Two reads in a row must return the same cached list object.

        Guards the caching itself: rebuilding the list on every step would be
        a performance regression in the hot path.
        """
        assert playground.elements is playground.elements
        assert playground.agents is playground.agents

    def test_cache_is_refreshed_after_invalidation(self, playground):
        """After an invalidation the cached list is rebuilt."""
        first = playground.elements
        assert first

        _add_wall(playground, (100, 100), (200, 100))
        second = playground.elements

        assert second is not first, "the cache should have been rebuilt"
        assert len(second) == len(first) + 1

    def test_cleanup_clears_the_collections(self, playground):
        """cleanup() must leave nothing behind in the cached lists."""
        _add_wall(playground, (100, 100), (200, 100))
        assert playground.elements

        playground.cleanup()

        assert playground.elements == []
        assert playground.agents == []
