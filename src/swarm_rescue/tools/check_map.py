from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.gui_sr import GuiSR

from maps.map_intermediate_01 import MyMapIntermediate01
from maps.map_complete_01 import MyMapComplete01
from maps.map_complete_02 import MyMapComplete02


class MyMap(MyMapComplete02):
    pass


class MyDrone(DroneAbstract):
    def define_message_for_all(self):
        pass

    def control(self):
        pass


if __name__ == "__main__":
    for environment_type in MyMap.environment_series:
        print("")
        print("*** Environment '{}'".format(environment_type.name.lower()))
        my_map = MyMap(environment_type)
        playground = my_map.construct_playground(drone_type=MyDrone)

        my_gui = GuiSR(playground=playground,
                       the_map=my_map,
                       use_mouse_measure=True)

        my_gui.run()
