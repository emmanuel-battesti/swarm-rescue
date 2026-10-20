"""
This program can be launched directly.
Example of how to use the headless mode, i.e. how to run a simulation without
opening any window.

Why headless is fast
--------------------
With a window, arcade runs its usual event loop, and `GuiSR` asks it to
dispatch one simulation step every `FRAME_RATE` (1/30 s), because a human has
to be able to *see* what happens. The simulation is then capped at
30 steps per second, whatever the machine is capable of.

With `headless=True`, nothing is displayed, so that cap is useless: the
simulation only runs as fast as the CPU allows. On a recent machine, expect
several hundred steps per second, i.e. several times faster than the windowed
mode (about x7 on current hardware) for the very same
code.

Only the presentation changes: the physics, the sensors, the drones, and the
scoring are the same in both modes.

Usage
-----
    # Headless run (default): the fastest way to run a simulation
    python examples/example_headless.py

    # Same run, with a window: useful to *see* what the drones do
    python examples/example_headless.py --gui

    # Run both and print the measured speed of each one
    python examples/example_headless.py --compare

    # Longer run, and a video recorded while running headless
    python examples/example_headless.py --steps 2000 --video /tmp/run.avi

Note: headless mode still needs an OpenGL context, so on a machine without any
display (a server, a container, a CI runner), run the example under a virtual
framebuffer:

    xvfb-run -s "-screen 0 1920x1080x24" python examples/example_headless.py

Same results in both modes
--------------------------
`--compare` also prints the scores of the two runs. They are identical, and
they have to be: the simulation is stepped, not timed. Nothing in the outcome
may depend on how fast the machine executed it. Collision damage is throttled
by a cooldown counted in simulation steps, not real seconds, so both modes
give the drones the same damage for the same trajectory.

Recording a video (`--video`) costs a full frame render per step, and brings
the headless mode back to roughly 60 steps/s. It stays faster than a window,
but record only when a video is really needed: measure, debug and tune
without it.

Note on the map below
--------------------
`MyMapHeadless` writes no exploration bookkeeping at all: no
`explored_map.initialize_walls(...)`, no `reset()`. The exploration score still
comes out right because `ExploredMap` initializes its own walls the first time
it is asked for them. A map only describes its playground.
"""

import argparse
import pathlib
import sys
from typing import List, Optional, Tuple, Type

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'examples/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.maps.walls_medium_01 import add_walls, add_boxes
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData

# Number of simulation steps of a run. A run stops on this limit, so the same
# number of steps is always simulated, whatever the mode: comparing the two
# modes then compares *time*, not *work*.
DEFAULT_NB_STEPS = 1000


class MyDroneHeadless(DroneAbstract):
    """
    A very simple drone: it flies forward and turns regularly.

    Nothing here depends on the display: the exact same drone code is used for
    a windowed run and for a headless one.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Turn for these many steps, then fly straight for these many steps.
        self._nb_steps_per_turn = 30

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self) -> CommandsDict:
        # A deterministic behavior: no random, so that the trajectory of the
        # drone does not depend on the mode it is simulated in.
        turning = (self.elapsed_timestep // self._nb_steps_per_turn) % 2 == 0

        command: CommandsDict = {"forward": 1.0,
                                 "lateral": 0.0,
                                 "rotation": 1.0 if turning else -1.0,
                                 "grasper": 0}

        return command


class MyMapHeadless(MapAbstract):

    def __init__(self,
                 drone_type: Type[DroneAbstract],
                 nb_steps: int = DEFAULT_NB_STEPS):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (1113, 750)

        # The run stops after this number of steps. This is what makes the two
        # modes comparable: the same amount of work, measured in time.
        self._max_timestep_limit = nb_steps
        # Long enough never to be reached: we want to measure the speed, not
        # to have the runs stopped by the wall clock.
        self._max_walltime_limit = 1000000

        self._rescue_center = RescueCenter(size=(210, 90))
        self._rescue_center_pos = ((440, 315), 0)

        self._wounded_persons_pos = [(-400, -250), (-200, -250), (0, -250),
                                     (200, -250), (400, -250)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._number_drones = 4
        self._drones_pos = [((-100, 250), 0.0),
                            ((-60, 250), 0.0),
                            ((-20, 250), 0.0),
                            ((20, 250), 0.0)]
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        self._playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(self._playground)
        add_boxes(self._playground)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            self._playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def run_once(headless: bool,
             nb_steps: int = DEFAULT_NB_STEPS,
             filename_video_capture: Optional[str] = None
             ) -> Tuple[int, float, float]:
    """
    Run one simulation and return (nb_steps, walltime, frequency).

    Args:
        headless (bool): True to run without any window, which is much faster.
        nb_steps (int): Number of simulation steps of the run.
        filename_video_capture (Optional[str]): File to record the run into,
            or None to record nothing.

    Returns:
        Tuple[int, float, float]: The number of steps simulated, the elapsed
        walltime in seconds, and the number of steps per second.
    """
    the_map = MyMapHeadless(drone_type=MyDroneHeadless, nb_steps=nb_steps)

    # The *only* difference between the two modes is this `headless` argument.
    #
    # - headless=True: the window is created but never shown, and the
    #                   simulation is not limited to FRAME_RATE steps/s.
    # - headless=False: the window is shown, and the simulation is capped at
    #                   FRAME_RATE (30) steps/s, so that a human can watch it.
    gui = GuiSR(the_map=the_map,
                headless=headless,
                filename_video_capture=filename_video_capture,
                )

    # Blocking call: it returns when the simulation is over.
    gui.run()

    nb_steps_done = gui.elapsed_timestep
    walltime = gui.elapsed_walltime
    # 'frequency' is the number of simulation steps per second of wall clock:
    # this is the figure to compare between the two modes.
    frequency = nb_steps_done / walltime if walltime > 0 else 0.0

    print(f"\trescued: {int(gui.rescued_number)}/{the_map.number_wounded_persons}, "
          f"health returned: {the_map.compute_score_health_returned() * 100:.1f}%, "
          f"exploration: {the_map.explored_map.score() * 100:.1f}%")
    print(f"\tsteps: {nb_steps_done}, "
          f"walltime: {walltime:.2f}s, "
          f"frequency: {frequency:.1f} steps/s")

    # Release the GPU resources of this run before the next one starts, so
    # that two runs can happen one after the other in the same process.
    playground = the_map.playground
    assert playground is not None, "The map has not been built."
    playground.cleanup()
    playground.close_window()

    return nb_steps_done, walltime, frequency


def main():
    parser = argparse.ArgumentParser(
        description="Example of the headless mode: run the simulation "
                    "without any window, which is much faster.")
    parser.add_argument("--steps", "-n", type=int, default=DEFAULT_NB_STEPS,
                        help=f"Number of simulation steps (default: "
                             f"{DEFAULT_NB_STEPS})")
    parser.add_argument("--gui", "-g", action="store_true",
                        help="Open a window instead of running headless")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Run headless, then with a window, and compare "
                             "the two speeds")
    parser.add_argument("--video", type=str, default=None,
                        help="Record the run into this video file")
    args = parser.parse_args()

    if args.compare:
        print(f"Headless run ({args.steps} steps)")
        _, headless_walltime, headless_freq = run_once(headless=True,
                                                       nb_steps=args.steps)

        print(f"\nWindowed run ({args.steps} steps)")
        _, windowed_walltime, windowed_freq = run_once(headless=False,
                                                       nb_steps=args.steps)

        print("\nSummary")
        print(f"\theadless: {headless_walltime:.2f}s "
              f"({headless_freq:.1f} steps/s)")
        print(f"\twindowed: {windowed_walltime:.2f}s "
              f"({windowed_freq:.1f} steps/s)")
        if headless_walltime > 0:
            print(f"\tspeedup: x{windowed_walltime / headless_walltime:.1f} "
                  f"in headless mode")
    else:
        mode = "windowed" if args.gui else "headless"
        print(f"{mode.capitalize()} run ({args.steps} steps)")
        run_once(headless=not args.gui,
                 nb_steps=args.steps,
                 filename_video_capture=args.video)


if __name__ == '__main__':
    main()
