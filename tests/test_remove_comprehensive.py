#!/usr/bin/env python3
"""
Removal scenarios for Playground.remove(), including the recursive paths.

`remove()` walks into related entities before doing its own work: an Agent
pulls in its base, a DronePart pulls in its devices, a PhysicalElement pulls
in its interactives and releases whatever grasps it. Removing a tree of
entities must therefore mark every one of them, and removing them again must
stay a no-op.

These tests complement `test_remove_protection.py`, which focuses on the
idempotence of a second removal.
"""
import pathlib
import sys
from typing import List, Type

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData


class DummyDrone(DroneAbstract):
    """Simple drone for testing"""
    def define_message_for_all(self):
        pass

    def control(self):
        pass


class MyMapTest(MapAbstract):
    """Test map with basic playground setup"""
    def __init__(
        self, drone_type: Type[DroneAbstract] = DummyDrone, with_rescue_center: bool = True
    ):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (1000, 1000)
        self._number_drones = 0
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        # Add rescue center if needed
        if with_rescue_center:
            self.rescue_center = RescueCenter(size=(100, 100))
            self._playground.add(self.rescue_center, ((0, 0), 0))
        else:
            self.rescue_center = None


def test_7_agent_with_base_recursive_removal():
    """Removing an Agent also removes its base."""
    the_map = MyMapTest()
    playground = the_map.playground

    misc_data = MiscData(size_area=(1000, 1000), number_drones=1)
    drone = DummyDrone(identifier=0, misc_data=misc_data)
    playground.add(drone, ((100, 100), 0))

    assert drone.base is not None
    base = drone.base
    assert base.removed is False

    playground.remove(drone, definitive=False)

    # The recursion into the base is the point of this test.
    assert drone.removed is True
    assert base.removed is True, "Removing an Agent must remove its base too"

    # ...and doing it again stays a no-op.
    playground.remove(drone, definitive=False)
    assert drone.removed is True
    assert base.removed is True


def test_8_physical_element_with_interactives():
    """A PhysicalElement is removed together with its interactives."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    interactives = list(wp.interactives)
    assert interactives, "The scenario needs a wounded person with interactives"

    playground.remove(wp, definitive=False)
    assert wp.removed is True

    for interactive in interactives:
        assert interactive.removed is True, \
            "Removing a PhysicalElement must remove its interactives too"

    # Second removal is still a no-op.
    playground.remove(wp, definitive=False)
    assert wp.removed is True


def test_9_remove_then_definitive_remove():
    """Going from non-definitive to definitive drops the entity for good."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    playground.remove(wp, definitive=False)
    assert wp in playground._elements
    assert wp.uid in playground._uids_to_entities

    # Escalating to definitive on an already-removed entity must work.
    playground.remove(wp, definitive=True)

    assert wp.removed is True
    assert wp not in playground._elements, \
        "A definitive removal drops the entity, even after a non-definitive one"
    assert wp.uid not in playground._uids_to_entities


def test_10_definitive_then_non_definitive():
    """The reverse order is safe too: definitive then non-definitive."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    playground.remove(wp, definitive=True)
    assert wp not in playground._elements
    assert wp.uid not in playground._uids_to_entities

    # Must not raise, and must not resurrect the entity.
    playground.remove(wp, definitive=False)

    assert wp.removed is True
    assert wp not in playground._elements
    assert wp.uid not in playground._uids_to_entities


def test_11_multiple_entities_with_cross_references():
    """A batch of entities can all be removed twice."""
    the_map = MyMapTest()
    playground = the_map.playground

    entities = []
    for i in range(5):
        wp = WoundedPerson(rescue_center=the_map.rescue_center)
        entities.append(wp)
        playground.add(wp, ((100 * (i + 1), 100), 0))

    for wp in entities:
        playground.remove(wp, definitive=False)

    assert all(e.removed for e in entities), "Every entity must be marked removed"

    elements_after_first = len(playground._elements)

    for wp in entities:
        playground.remove(wp, definitive=False)

    assert all(e.removed for e in entities)
    assert len(playground._elements) == elements_after_first, \
        "The second pass must not change the playground any further"


def test_12_rescue_center_removal():
    """A RescueCenter is removable, and idempotently so."""
    the_map = MyMapTest(with_rescue_center=False)
    playground = the_map.playground

    rescue_center = RescueCenter(size=(100, 100))
    playground.add(rescue_center, ((0, 0), 0))

    assert rescue_center.removed is False

    playground.remove(rescue_center, definitive=False)
    assert rescue_center.removed is True
    assert rescue_center in playground._elements

    playground.remove(rescue_center, definitive=False)
    assert rescue_center.removed is True
    assert rescue_center in playground._elements


def test_13_edge_case_cleanup_on_empty():
    """cleanup() on a playground whose only entity is already removed."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    playground.remove(wp, definitive=False)
    assert wp.uid in playground._uids_to_entities

    playground.cleanup()

    assert wp.uid not in playground._uids_to_entities
    assert wp not in playground._elements


def test_14_alternating_remove_patterns():
    """Alternating non-definitive removal attempts over several entities."""
    the_map = MyMapTest()
    playground = the_map.playground

    entities = []
    for i in range(4):
        wp = WoundedPerson(rescue_center=the_map.rescue_center)
        entities.append(wp)
        playground.add(wp, ((100 * (i + 1), 100), 0))

    for wp in entities:
        playground.remove(wp, definitive=False)

    elements_after_first = len(playground._elements)

    for wp in entities:
        playground.remove(wp, definitive=False)

    assert all(e.removed for e in entities)
    assert len(playground._elements) == elements_after_first


def test_15_definitive_removal_bug():
    """A double definitive removal must not raise KeyError.

    Regression test: `_remove_from_mappings()` used to `pop()` the uid
    unconditionally, so a second definitive removal raised `KeyError`. It now
    returns early when the uid is already gone.
    """
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    playground.remove(wp, definitive=True)
    assert wp.uid not in playground._uids_to_entities

    # Must not raise KeyError.
    playground.remove(wp, definitive=True)

    assert wp.removed is True
    assert wp not in playground._elements
    assert wp.uid not in playground._uids_to_entities


