import gc
import math
import pathlib
import sys
from typing import List, Type, Optional
import numpy as np

# Insert the parent directory of the current file's directory into sys.path.
# This allows Python to locate modules that are one level above the current
# script, in this case simulation.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.return_area import ReturnArea
from swarm_rescue.simulation.elements.sensor_disablers import ZoneType, NoComZone
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.reporting.evaluation import ZonesConfig, EvalPlan, EvalConfig
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.pose import Pose

from swarm_rescue.maps.walls_final_2025_26_01 import add_walls, add_boxes


class MapFinal_2025_26_01(MapAbstract):

    def __init__(self,
                 drone_type: Type[DroneAbstract],
                 zones_config: ZonesConfig = (),
                 seed: Optional[int] = None):
        super().__init__(drone_type, zones_config, seed=seed)
        self._max_timestep_limit = 7200
        self._max_walltime_limit = 1440  # In seconds

        # PARAMETERS MAP
        self._size_area = (1700, 1100)

        self._return_area = ReturnArea(size=(114, 234))
        self._return_area_pos = ((-102, 88), 0)

        self._rescue_center = RescueCenter(size=(86, 124))
        self._rescue_center_pos = ((-1, 36), 0)

        self._no_com_zone_1 = NoComZone(size=(618, 997))
        self._no_com_zone_pos_1 = ((533, 44), 0)

        self._wounded_persons_pos = \
            [(-246, 520), (-283, 520), (798, -496), (-778, -495), (-652, -413),
             (-725, -407), (-674, -348), (487, -222), (26, -165), (488, 4),
             (-144, 187), (184, 249), (-651, 312), (322, 445)]

        self._wounded_persons_path = [[(-246, 520), (135, 520)],
                                      [(-283, 520), (-819, 520)]]

        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        # POSITIONS OF THE DRONES
        self._number_drones = 10
        # They are positioned in a square whose side size depends on the total
        # number of drones.
        start_area_drones = (-101, 20)
        nb_per_side = 2
        dist_inter_drone = 40.0
        # print("nb_per_side", nb_per_side)
        # print("dist_inter_drone", dist_inter_drone)
        sx = start_area_drones[0] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        sy = start_area_drones[1] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        # print("sx", sx, "sy", sy)

        self._drones_pos = []
        for i in range(self._number_drones):
            x = sx + (float(i) % nb_per_side) * dist_inter_drone
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_drone
            angle = self._rng.uniform(-math.pi, math.pi)
            self._drones_pos.append(((x, y), angle))

        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(
            size=self._size_area,
            border_thickness=9,
            seed=self._seed
        )

        self._playground.add(self._return_area, self._return_area_pos)
        self._playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(self._playground)
        add_boxes(self._playground)

        # DISABLER ZONES
        if ZoneType.NO_COM_ZONE in self._zones_config:
            self._playground.add(self._no_com_zone_1, self._no_com_zone_pos_1)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            init_pos = (self._wounded_persons_pos[i], 0)
            self._playground.add(wounded_person, init_pos)

            wounded_person.add_pose_to_path(Pose(np.array(init_pos[0])))
            if i < len(self._wounded_persons_path):
                for pt in self._wounded_persons_path[i]:
                    wounded_person.add_pose_to_path(Pose(np.array(list(pt))))

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def main():
    eval_plan = EvalPlan()

    zones_config = ()
    eval_config = EvalConfig(map_name="MapFinal_2025_26_01", zones_config=zones_config)
    eval_plan.add(eval_config=eval_config)

    zones_config = (ZoneType.NO_COM_ZONE,)
    eval_config = EvalConfig(map_name="MapFinal_2025_26_01", zones_config=zones_config)
    eval_plan.add(eval_config=eval_config)

    for one_eval in eval_plan.list_eval_config:
        gc.collect()

        # Retrieve the class object from the global namespace using its name
        map_class = globals().get(one_eval.map_name)
        if map_class is None:
            print(f"Unknown map type '{one_eval.map_name}', skipping.")
            continue
        # Instantiate the map class with the provided zones configuration
        the_map = map_class(drone_type=DroneMotionless, zones_config=one_eval.zones_config)

        gui = GuiSR(the_map=the_map,
                    use_mouse_measure=True,
                    )
        gui.run()


if __name__ == '__main__':
    main()
