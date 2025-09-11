from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.reporting.evaluation import EvalPlan, ZonesConfig, EvalConfig

from swarm_rescue.maps.map_intermediate_01 import MyMapIntermediate01
from swarm_rescue.maps.map_final_2022_23 import MyMapFinal2022_23
from swarm_rescue.maps.map_medium_01 import MyMapMedium01
from swarm_rescue.maps.map_medium_02 import MyMapMedium02


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


if __name__ == "__main__":
    """
    Runs a GUI to check the map visually with a dummy drone.
    """
    eval_plan = EvalPlan()

    zones_config: ZonesConfig = ()
    eval_config = EvalConfig(map_name="MyMapMedium02", zones_config=zones_config)
    eval_plan.add(eval_config=eval_config)

    for eval_config in eval_plan.list_eval_config:
        print("")
        print(f"*** Map {eval_config.map_name}, "
              f"zones \'{eval_config.zones_name_for_filename}\'")
        my_map = eval_config.map_type(drone_type=MyDrone, eval_config.zones_config)

        my_gui = GuiSR(the_map=my_map,
                       use_mouse_measure=True)

        my_gui.run()
