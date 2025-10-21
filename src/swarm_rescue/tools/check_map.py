import gc

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.reporting.evaluation import EvalPlan, ZonesConfig, EvalConfig

from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.maps.map_final_2022_23 import MapFinal2022_23
from swarm_rescue.maps.map_medium_01 import MapMedium01
from swarm_rescue.maps.map_medium_02 import MapMedium02


class MyDrone(DroneAbstract):
    """
    Dummy drone class for map checking.
    """
    def define_message_for_all(self) -> None:
        """
        Defines messages for all drones (not implemented).
        """
        pass

    def control(self) -> CommandsDict:
        """
        Returns control commands for the drone (not implemented).
        """
        pass


def main():
    """
    Runs a GUI to check the map visually with a dummy drone.
    """
    eval_plan = EvalPlan()

    zones_config: ZonesConfig = ()
    eval_config = EvalConfig(map_name="MapMedium02", zones_config=zones_config)
    eval_plan.add(eval_config=eval_config)

    for one_eval in eval_plan.list_eval_config:
        gc.collect()
        print("")
        print(f"*** Map {one_eval.map_name}, "
              f"zones \'{one_eval.zones_name_for_filename}\'")
        # Retrieve the class object from the global namespace using its name
        map_class = globals().get(one_eval.map_name)
        # Instantiate the map class with the provided zones configuration
        the_map = map_class(drone_type=MyDrone, zones_config=one_eval.zones_config)

        my_gui = GuiSR(the_map=the_map,
                       use_mouse_measure=True)

        my_gui.run()

if __name__ == '__main__':
    main()