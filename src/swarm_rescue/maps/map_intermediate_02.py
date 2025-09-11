import gc
import math
import random
import sys
from pathlib import Path
from typing import List, Type

# Insert the parent directory of the current file's directory into sys.path.
# This allows Python to locate modules that are one level above the current
# script, in this case spg_overlay.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.drone_motionless import DroneMotionless
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.entities.return_area import ReturnArea
from spg_overlay.entities.sensor_disablers import ZoneType, NoComZone, KillZone
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.evaluation import ZonesConfig, EvalConfig, EvalPlan
from spg_overlay.utils.misc_data import MiscData


class MyMapIntermediate02(MapAbstract):

    def __init__(self, zones_config: ZonesConfig = ()):
        super().__init__(zones_config)
        self._max_timestep_limit = 2700
        self._max_walltime_limit = 540

        # PARAMETERS MAP
        self._size_area = (1200, 500)

        self._return_area = ReturnArea(size=(200, 240))
        self._return_area_pos = ((496, 40), 0)

        self._rescue_center = RescueCenter(size=(200, 80))
        self._rescue_center_pos = ((496, 206), 0)

        self._no_com_zone = NoComZone(size=(330, 500))
        self._no_com_zone_pos = ((-159, 0), 0)

        self._kill_zone = KillZone(size=(68, 360))
        self._kill_zone_pos = ((-484, 0), 0)

        self._wounded_persons_pos = \
            [(-555, 188), (-420, 188), (-285, 188), (-150, 188), (-15, 188),
             (120, 188), (255, 188), (-555, 63), (-420, 63), (-285, 63),
             (-150, 63), (-15, 63), (120, 63), (255, 63), (-555, -62),
             (-420, -62), (-285, -62), (-150, -62), (-15, -62), (120, -62),
             (255, -62), (-555, -187), (-420, -187), (-285, -187),
             (-150, -187), (-15, -187), (120, -187), (255, -187)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._number_drones = 10
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (496, 100)
        nb_per_side = math.ceil(math.sqrt(float(self._number_drones)))
        dist_inter_drone = 50.0
        # print("nb_per_side", nb_per_side)
        # print("dist_inter_drone", dist_inter_drone)
        sx = start_area_drones[0] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        sy = start_area_drones[1] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        # print("sx", sx, "sy", sy)

        self._drones_pos = []
        for i in range(self._number_drones):
            x = sx + (float(i) % nb_per_side) * dist_inter_drone
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_drone
            angle = random.uniform(-math.pi, math.pi)
            self._drones_pos.append(((x, y), angle))

        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        playground.add(self._return_area, self._return_area_pos)
        playground.add(self._rescue_center, self._rescue_center_pos)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        if ZoneType.NO_COM_ZONE in self._zones_config:
            playground.add(self._no_com_zone, self._no_com_zone_pos)

        if ZoneType.KILL_ZONE in self._zones_config:
            playground.add(self._kill_zone, self._kill_zone_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    eval_plan = EvalPlan()

    zones_config: ZonesConfig = ()
    eval_config = EvalConfig(map_name="MyMapIntermediate02", zones_config=zones_config, nb_rounds=2)
    eval_plan.add(eval_config=eval_config)

    zones_config: ZonesConfig = (ZoneType.NO_COM_ZONE, ZoneType.KILL_ZONE)
    eval_config = EvalConfig(map_name="MyMapIntermediate02", zones_config=zones_config, nb_rounds=2)
    eval_plan.add(eval_config=eval_config)

    for one_eval in eval_plan.list_eval_config:
        gc.collect()

        # Retrieve the class object from the global namespace using its name
        map_class = globals().get(one_eval.map_name)
        # Instantiate the map class with the provided zones configuration
        my_map = map_class(one_eval.zones_config)

        my_playground = my_map.construct_playground(drone_type=DroneMotionless)

        gui = GuiSR(playground=my_playground,
                    the_map=my_map,
                    use_mouse_measure=True,
                    )
        gui.run()


if __name__ == '__main__':
    main()
