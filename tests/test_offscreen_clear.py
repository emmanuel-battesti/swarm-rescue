"""
An offscreen frame must be erased completely, whatever the window is doing.

`glClear` obeys the scissor box, and arcade keeps that box aligned with the
*window* viewport: `GuiSR` sets it to the letterboxed map area so the letterbox
color survives outside it. The framebuffer used by
`update_and_draw_in_framebuffer` is sized to the *map*, so the window's box
decided how much of it was erased -- three quarters of it on a 600x400 map in a
300x200 window.

Nothing crashes and the frame is still drawn, so the only symptom is that the
frame keeps the previous one: a moving sprite drags a trail behind it in the
recorded video and in the reported screenshot, and `render_uids` -- the same
framebuffer, read by the ray sensors -- carries a stale entity where a drone
used to be.

These tests pin the property on the raw framebuffer, without a video codec in
the way.
"""

import pathlib
import sys

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import numpy as np

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData

SIZE = (600, 400)


class _Drone(DroneAbstract):
    def define_message_for_all(self):
        pass

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class _Map(MapAbstract):
    def __init__(self, drone_type):
        super().__init__(drone_type=drone_type)
        self._size_area = SIZE
        self._max_timestep_limit = 10
        self._max_walltime_limit = 1000
        self._number_drones = 1
        self._drones_pos = [((0.0, 0.0), 0.0)]
        self._drones = []
        self._number_wounded_persons = 0

        self._playground = ClosedPlayground(size=self._size_area)
        misc_data = MiscData(size_area=self._size_area, number_drones=1,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        self._drones.append(drone_type(identifier=0, misc_data=misc_data))
        self._playground.add(self._drones[0], self._drones_pos[0])


def _build_gui():
    the_map = _Map(drone_type=_Drone)
    gui = GuiSR(the_map=the_map, headless=True)
    return the_map, gui


def _shot(gui, drone, x):
    """Move the drone, re-render offscreen, and return the raw framebuffer."""
    drone.move_to(((x, 0.0), 0.0), allow_overlapping=True)
    gui.update_and_draw_in_framebuffer(force=True)
    return np.array(gui.get_np_img())


def _teardown(the_map):
    the_map.playground.cleanup()
    the_map.playground.close_window()


def test_a_moved_drone_leaves_nothing_behind():
    """
    The trail itself: where the drone was, the next frame must be background.

    World x=-200 is column 100 of a 600x400 map whose center is column 300, so
    the region checked is the one the drone has just left.
    """
    the_map, gui = _build_gui()
    try:
        drone = the_map.drones[0]
        background = np.array(the_map.playground.background)

        first = _shot(gui, drone, -200.0)
        second = _shot(gui, drone, 200.0)

        # The drone really was there in the first frame, otherwise the second
        # assertion below would be satisfied by a frame that draws nothing.
        was_painted = first[185:220, 85:140]
        assert (np.abs(was_painted.astype(int)
                       - background).sum(axis=-1) > 0).sum() > 0, (
            "precondition: the drone is not visible where the test looks"
        )

        left_behind = second[185:220, 85:140]
        still_painted = (np.abs(left_behind.astype(int)
                               - background).sum(axis=-1) > 0).sum()

        assert still_painted == 0, (
            f"{still_painted} pixels of the drone's previous position are still "
            f"painted in the next frame: the offscreen framebuffer is not fully "
            f"cleared, so sprites drag a trail behind them"
        )
    finally:
        _teardown(the_map)


def test_the_drone_is_actually_drawn():
    """
    Guard against the test above passing on an empty frame.

    Without a drawn drone there would be nothing to leave behind, and the
    previous test would be satisfied by a framebuffer that renders nothing at
    all.
    """
    the_map, gui = _build_gui()
    try:
        drone = the_map.drones[0]
        left = _shot(gui, drone, -200.0)
        right = _shot(gui, drone, 200.0)

        assert not np.array_equal(left[185:220, 85:140],
                                  right[185:220, 485:545]), (
            "the two renders are identical: the test would pass without ever "
            "drawing a drone"
        )
    finally:
        _teardown(the_map)


def test_the_scissor_is_restored_after_an_offscreen_render():
    """
    The window does want its scissor -- it is what preserves the letterbox.

    Suspending it around the offscreen render must not leave it off for the
    window that comes next.
    """
    from pyglet.gl import GL_SCISSOR_TEST, glIsEnabled

    the_map, gui = _build_gui()
    try:
        assert glIsEnabled(GL_SCISSOR_TEST), (
            "precondition: the scissor test is on before the offscreen render"
        )

        _shot(gui, the_map.drones[0], 0.0)

        assert glIsEnabled(GL_SCISSOR_TEST), (
            "the offscreen render left the scissor test disabled, so the "
            "window would no longer clip its drawing to the map area"
        )
    finally:
        _teardown(the_map)
