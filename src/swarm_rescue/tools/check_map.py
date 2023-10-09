from spg_overlay.entities.sensor_disablers import ZoneType
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.reporting.evaluation import EvalPlan, ZonesConfig, EvalConfig

from maps.map_intermediate_01 import MyMapIntermediate01
from maps.map_final_2023 import MyMapFinal
from maps.map_medium_01 import MyMapMedium01
from maps.map_medium_02 import MyMapMedium02


class MyDrone(DroneAbstract):
    def define_message_for_all(self):
        pass

    def control(self):
        pass


if __name__ == "__main__":
    eval_plan = EvalPlan()

    zones_config: ZonesConfig = ()
    eval_config = EvalConfig(map_type=MyMapMedium02, zones_config=zones_config)
    eval_plan.add(eval_config=eval_config)

    for eval_config in eval_plan.list_eval_config:
        print("")
        print(f"*** Map {eval_config.map_name}, zones \'{eval_config.zones_name_for_filename}\'")
        my_map = eval_config.map_type(eval_config.zones_config)
        playground = my_map.construct_playground(drone_type=MyDrone)

        my_gui = GuiSR(playground=playground,
                       the_map=my_map,
                       use_mouse_measure=True)

        my_gui.run()
