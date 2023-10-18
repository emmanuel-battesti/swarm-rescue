"""
This program can be launched directly.
Example of how to control several drones
"""

import math
import os
import random
import sys
from typing import List, Type

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.entities.drone_distance_sensors import DroneSemanticSensor
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def process_semantic_sensor(self):
        detection_semantic = self.semantic_values()

        print("********************************************")
        if detection_semantic is not None:
            for data in detection_semantic:
                if data.distance > 60:
                    continue

                if data.entity_type == DroneSemanticSensor.TypeEntity.WALL:
                    print("type: wall, angle: {:.2f}, d: {:.1f}".format(data.angle, data.distance))
                elif data.entity_type == DroneSemanticSensor.TypeEntity.OTHER:
                    print("type: other, angle: {:.2f}, d: {:.1f}".format(data.angle, data.distance))
                elif data.entity_type == DroneSemanticSensor.TypeEntity.WOUNDED_PERSON:
                    print("type: wounded, angle: {:.2f}, d: {:.1f}".format(data.angle, data.distance))
                elif data.entity_type == DroneSemanticSensor.TypeEntity.DRONE:
                    print("type: drone, angle: {:.2f}, d: {:.1f}".format(data.angle, data.distance))

    def control(self):
        if self.identifier == 0:
            self.process_semantic_sensor()


class MyMap(MapAbstract):
    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (700, 700)

        # WOUNDED PERSONS
        self._number_wounded_persons = 30
        self._wounded_persons_pos = []
        self._wounded_persons: List[WoundedPerson] = []

        start_area = (0.0, 0.0)
        nb_per_side = math.ceil(math.sqrt(float(self._number_wounded_persons)))
        dist_inter_wounded = 100.0
        sx = start_area[0] - (nb_per_side - 1) * 0.5 * dist_inter_wounded
        sy = start_area[1] - (nb_per_side - 1) * 0.5 * dist_inter_wounded

        for i in range(self._number_wounded_persons):
            x = sx + (float(i) % nb_per_side) * dist_inter_wounded
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_wounded
            pos = ((x, y), random.uniform(-math.pi, math.pi))
            self._wounded_persons_pos.append(pos)

        # POSITIONS OF THE DRONES
        self._number_drones = 20
        self._drones_pos = []
        for i in range(self._number_drones):
            pos = ((random.uniform(-self._size_area[0] / 2, self._size_area[0] / 2),
                    random.uniform(-self._size_area[1] / 2, self._size_area[1] / 2)),
                   random.uniform(-math.pi, math.pi))
            self._drones_pos.append(pos)

        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=None)
            self._wounded_persons.append(wounded_person)
            pos = self._wounded_persons_pos[i]
            playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    my_map = MyMap()
    playground = my_map.construct_playground(drone_type=MyDrone)
    gui = GuiSR(playground=playground,
                the_map=my_map,
                draw_semantic_rays=True,
                use_keyboard=True,
                use_mouse_measure=True,
                enable_visu_noises=False,
                )
    gui.run()


if __name__ == '__main__':
    main()
