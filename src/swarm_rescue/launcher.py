import gc
from typing import Tuple

from spg_overlay.entities.sensor_disablers import ZoneType
from spg_overlay.utils.constants import DRONE_INITIAL_HEALTH
from spg_overlay.reporting.evaluation import EvalConfig, EvalPlan, ZonesConfig
from spg_overlay.reporting.score_manager import ScoreManager
from spg_overlay.reporting.data_saver import DataSaver
from spg_overlay.reporting.screen_recorder import ScreenRecorder
from spg_overlay.reporting.team_info import TeamInfo
from spg_overlay.gui_map.gui_sr import GuiSR

from maps.map_intermediate_01 import MyMapIntermediate01
from maps.map_intermediate_02 import MyMapIntermediate02
from maps.map_final_2023 import MyMapFinal
from maps.map_medium_01 import MyMapMedium01
from maps.map_medium_02 import MyMapMedium02

from solutions.my_drone_eval import MyDroneEval


class MyDrone(MyDroneEval):
    pass


class Launcher:
    """
    The Launcher class is responsible for running a simulation of drone rescue sessions. It creates an instance of the
    map with a specified zone type, constructs a playground using the construct_playground method of the map
    class, and initializes a GUI with the playground and map. It then runs the GUI, allowing the user to interact
    with it. After the GUI finishes, it calculates the score for the exploration of the map and saves the images and
    data related to the round.

    Fields
        nb_rounds: The number of rounds to run in the simulation.
        team_info: An instance of the TeamInfo class that stores team information.
        number_drones: The number of drones in the simulation.
        time_step_limit: The maximum number of time steps in the simulation.
        real_time_limit: The maximum elapsed real time in the simulation.
        number_wounded_persons: The number of wounded persons in the simulation.
        size_area: The size of the simulation area.
        score_manager: An instance of the ScoreManager class that calculates the final score.
        data_saver: An instance of the DataSaver class that saves images and data related to the simulation.
        video_capture_enabled: A boolean indicating whether video capture is enabled or not.
    """

    def __init__(self):

        """
        Here you can fill in the evaluation plan ("evalplan") yourself, adding or removing configurations.
        A configuration is defined by a map of the environment and whether or not there are zones of difficulty.
        """

        self.team_info = TeamInfo()
        self.eval_plan = EvalPlan()

        eval_config = EvalConfig(map_type=MyMapIntermediate01, nb_rounds=2)
        self.eval_plan.add(eval_config=eval_config)

        eval_config = EvalConfig(map_type=MyMapIntermediate02)
        self.eval_plan.add(eval_config=eval_config)

        zones_config: ZonesConfig = ()
        eval_config = EvalConfig(map_type=MyMapMedium01, zones_config=zones_config, nb_rounds=1, config_weight=1)
        self.eval_plan.add(eval_config=eval_config)

        zones_config: ZonesConfig = (ZoneType.NO_COM_ZONE, ZoneType.NO_GPS_ZONE, ZoneType.KILL_ZONE)
        eval_config = EvalConfig(map_type=MyMapMedium01, zones_config=zones_config, nb_rounds=1, config_weight=1)
        self.eval_plan.add(eval_config=eval_config)

        zones_config: ZonesConfig = (ZoneType.NO_COM_ZONE, ZoneType.NO_GPS_ZONE, ZoneType.KILL_ZONE)
        eval_config = EvalConfig(map_type=MyMapMedium02, zones_config=zones_config, nb_rounds=1, config_weight=1)
        self.eval_plan.add(eval_config=eval_config)

        self.number_drones = None
        self.time_step_limit = None
        self.real_time_limit = None
        self.number_wounded_persons = None
        self.size_area = None

        self.score_manager = None

        self.data_saver = DataSaver(self.team_info, enabled=False)
        self.video_capture_enabled = False

    def one_round(self, eval_config: EvalConfig, num_round: int):
        """
        The one_round method is responsible for running a single round of the session. It creates an instance of the
        map class with the specified eval_config, constructs a playground using the construct_playground method
        of the map class, and initializes a GUI with the playground and map. It then runs the GUI, which allows the
        user to interact with. After the GUI finishes, it calculates the score for the exploration of the map and saves
        the images and data related to the round.
        """
        my_map = eval_config.map_type(eval_config.zones_config)
        self.number_drones = my_map.number_drones
        self.time_step_limit = my_map.time_step_limit
        self.real_time_limit = my_map.real_time_limit
        self.number_wounded_persons = my_map.number_wounded_persons
        self.size_area = my_map.size_area

        self.score_manager = ScoreManager(number_drones=self.number_drones,
                                          time_step_limit=self.time_step_limit,
                                          real_time_limit=self.real_time_limit,
                                          total_number_wounded_persons=self.number_wounded_persons)

        playground = my_map.construct_playground(drone_type=MyDrone)

        num_round_str = str(num_round)
        team_number_str = str(self.team_info.team_number).zfill(2)
        if self.video_capture_enabled:
            filename_video_capture = (f"{self.data_saver.path}/"
                                      f"/screen_{eval_config.map_name}_{eval_config.zones_name_for_filename}"
                                      f"_rd{num_round_str}_team{team_number_str}.avi")
        else:
            filename_video_capture = None

        my_gui = GuiSR(playground=playground,
                       the_map=my_map,
                       draw_interactive=False,
                       filename_video_capture=filename_video_capture)

        my_map.explored_map.reset()

        # this function below is a blocking function until the round is finished
        my_gui.run()

        score_exploration = my_map.explored_map.score() * 100.0

        last_image_explo_lines = my_map.explored_map.get_pretty_map_explo_lines()
        last_image_explo_zones = my_map.explored_map.get_pretty_map_explo_zones()
        self.data_saver.save_images(my_gui.last_image,
                                    last_image_explo_lines,
                                    last_image_explo_zones,
                                    eval_config.map_name,
                                    eval_config.zones_name_for_filename,
                                    num_round)

        return (my_gui.percent_drones_destroyed,
                my_gui.mean_drones_health,
                my_gui.elapsed_time,
                my_gui.rescued_all_time_step,
                score_exploration, my_gui.rescued_number,
                my_gui.real_time_elapsed,
                my_gui.real_time_limit_reached)

    def go(self):
        """
        The go method in the Launcher class is responsible for running the simulation for different eval_config,
         and calculating the score for each one.
        """
        for eval_config in self.eval_plan.list_eval_config:
            gc.collect()
            print("")

            if not isinstance(eval_config.zones_config, Tuple) and not isinstance(eval_config.zones_config[0], Tuple):
                raise ValueError("Invalid eval_config.zones_config. It should be a tuple of tuples of ZoneType.")

            print(f"*** Map: {eval_config.map_name}, special zones: {eval_config.zones_name_casual}")

            for num_round in range(eval_config.nb_rounds):
                gc.collect()
                result = self.one_round(eval_config, num_round + 1)
                (percent_drones_destroyed, mean_drones_health, elapsed_time_step, rescued_all_time_step,
                 score_exploration, rescued_number, real_time_elapsed, real_time_limit_reached) = result

                result_score = self.score_manager.compute_score(rescued_number,
                                                                score_exploration,
                                                                rescued_all_time_step)
                (round_score, percent_rescued, score_time_step) = result_score

                print(
                    f"\t* Round n°{num_round + 1}/{eval_config.nb_rounds}: "
                    f"\n\t\trescued nb: {int(rescued_number)}/{self.number_wounded_persons}, "
                    f"explor. score: {score_exploration:.0f}%, "
                    f"real time elapsed: {real_time_elapsed:.0f}s/{self.real_time_limit}s, "
                    f"elapse time: {elapsed_time_step}/{self.time_step_limit} steps, "
                    f"time to rescue all: {rescued_all_time_step} steps."
                    f"\n\t\tpercent of drones destroyed: {percent_drones_destroyed:.1f} %, "
                    f"mean drones health: {mean_drones_health:.1f}/{DRONE_INITIAL_HEALTH}."
                    f"\n\t\tround score: {round_score:.1f}%, "
                    f"frequency: {elapsed_time_step / real_time_elapsed:.2f} steps/s.")
                if real_time_limit_reached:
                    print(f"\t\tThe real time limit of {self.real_time_limit}s is reached first.")

                self.data_saver.save_one_round(eval_config,
                                               num_round + 1,
                                               percent_drones_destroyed,
                                               mean_drones_health,
                                               percent_rescued,
                                               score_exploration,
                                               elapsed_time_step,
                                               real_time_elapsed,
                                               rescued_all_time_step,
                                               score_time_step,
                                               round_score)
        self.data_saver.generate_pdf_report()


if __name__ == "__main__":
    gc.disable()
    launcher = Launcher()
    launcher.go()
