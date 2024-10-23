import argparse
import gc
import os
import sys
from typing import Tuple
import traceback

from spg_overlay.entities.sensor_disablers import ZoneType
from spg_overlay.reporting.result_path_creator import ResultPathCreator
from spg_overlay.utils.constants import DRONE_INITIAL_HEALTH
from spg_overlay.reporting.evaluation import EvalConfig, EvalPlan, ZonesConfig
from spg_overlay.reporting.score_manager import ScoreManager
from spg_overlay.reporting.data_saver import DataSaver
from spg_overlay.reporting.team_info import TeamInfo
from spg_overlay.gui_map.gui_sr import GuiSR

from maps.map_intermediate_01 import MyMapIntermediate01
from maps.map_intermediate_02 import MyMapIntermediate02
from maps.map_final_2022_23 import MyMapFinal2022_23
from maps.map_medium_01 import MyMapMedium01
from maps.map_medium_02 import MyMapMedium02

from solutions.my_drone_eval import MyDroneEval


class MyDrone(MyDroneEval):
    pass


class Launcher:
    """
    The Launcher class is responsible for running a simulation of drone rescue
    sessions. It creates an instance of the map with a specified zone type,
    constructs a playground using the construct_playground method of the map
    class, and initializes a GUI with the playground and map. It then runs the
    GUI, allowing the user to interact with it. After the GUI finishes, it
    calculates the score for the exploration of the map and saves the images
    and data related to the round.

    Fields
        nb_rounds: The number of rounds to run in the simulation.
        team_info: An instance of the TeamInfo class that stores team
        information.
        number_drones: The number of drones in the simulation.
        max_timestep_limit: The maximum number of time steps in the simulation.
        max_walltime_limit: The maximum elapsed real time or walltime in the
        simulation.
        number_wounded_persons: The number of wounded persons in the simulation.
        size_area: The size of the simulation area.
        score_manager: An instance of the ScoreManager class that calculates
        the final score.
        data_saver: An instance of the DataSaver class that saves images and
        data related to the simulation.
        video_capture_enabled: A boolean indicating whether video capture is
        enabled or not.
    """

    def __init__(self):

        """
        Here you can fill in the evaluation plan ("evalplan") yourself, adding
        or removing configurations.
        A configuration is defined by a map of the environment and whether or
        not there are zones of difficulty.
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
        self.max_timestep_limit = None
        self.max_walltime_limit = None
        self.number_wounded_persons = None
        self.size_area = None

        self.score_manager = None

        # Set this value to True to generate stat data and pdf report
        stat_saving_enabled = False
        # Set this value to True to generate a video of the mission
        self.video_capture_enabled = False

        self.result_path = None
        if stat_saving_enabled or self.video_capture_enabled:
            rpc = ResultPathCreator(self.team_info)
            self.result_path = rpc.path
        self.data_saver = DataSaver(team_info=self.team_info,
                                    result_path=self.result_path,
                                    enabled=stat_saving_enabled)

    def one_round(self, eval_config: EvalConfig, num_round: int, hide_solution_output: bool = False):
        """
        The one_round method is responsible for running a single round of the
        session. It creates an instance of the map class with the specified
        eval_config, constructs a playground using the construct_playground
        method of the map class, and initializes a GUI with the playground and
        map. It then runs the GUI, which allows the user to interact with.
        After the GUI finishes, it calculates the score for the exploration of
        the map and saves the images and data related to the round.
        """
        print("\n********************************")

        my_map = eval_config.map_type(eval_config.zones_config)
        self.number_drones = my_map.number_drones
        self.max_timestep_limit = my_map.max_timestep_limit
        self.max_walltime_limit = my_map.max_walltime_limit
        self.number_wounded_persons = my_map.number_wounded_persons
        self.size_area = my_map.size_area

        self.score_manager = ScoreManager(number_drones=self.number_drones,
                                          max_timestep_limit=self.max_timestep_limit,
                                          max_walltime_limit=self.max_walltime_limit,
                                          total_number_wounded_persons=self.number_wounded_persons)

        my_playground = my_map.construct_playground(drone_type=MyDrone)

        num_round_str = str(num_round)
        if self.video_capture_enabled:
            try:
                os.makedirs(self.result_path + "/videos/", exist_ok=True)
            except FileExistsError as error:
                print(error)
            filename_video_capture = (f"{self.result_path}/videos/"
                                      f"team{self.team_info.team_number_str}_"
                                      f"{eval_config.map_name}_"
                                      f"{eval_config.zones_name_for_filename}_"
                                      f"rd{num_round_str}"
                                      f".avi")
        else:
            filename_video_capture = None

        my_gui = GuiSR(playground=my_playground,
                       the_map=my_map,
                       draw_interactive=False,
                       filename_video_capture=filename_video_capture)

        window_title = (f"Team: {self.team_info.team_number_str}   -   "
                        f"Map: {type(my_map).__name__}   -   "
                        f"Round: {num_round_str}")
        my_gui.set_caption(window_title)

        my_map.explored_map.reset()

        has_crashed = False
        error_msg = ""

        if hide_solution_output:
            original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')

        try:
            # this function below is a blocking function until the round is finished
            my_gui.run()
        except Exception as error:
            error_msg = traceback.format_exc()
            my_gui.close()
            has_crashed = True
        finally:
            if hide_solution_output:
                sys.stdout.close()
                sys.stdout = original_stdout

        if has_crashed:
            print(error_msg)

        score_exploration = my_map.explored_map.score() * 100.0
        score_health_returned = my_map.compute_score_health_returned() * 100

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
                my_gui.elapsed_timestep,
                my_gui.full_rescue_timestep,
                score_exploration,
                my_gui.rescued_number,
                score_health_returned,
                my_gui.elapsed_walltime,
                my_gui.is_max_walltime_limit_reached,
                has_crashed)

    def go(self, stop_at_first_crash: bool = False, hide_solution_output: bool = False):
        """
        The go method in the Launcher class is responsible for running the simulation for different eval_config,
         and calculating the score for each one.
        """
        ok = True

        for eval_config in self.eval_plan.list_eval_config:
            gc.collect()
            print("")

            if not isinstance(eval_config.zones_config, Tuple) and not isinstance(eval_config.zones_config[0], Tuple):
                raise ValueError("Invalid eval_config.zones_config. It should be a tuple of tuples of ZoneType.")

            print(f"////////////////////////////////////////////////////////////////////////////////////////////")
            print(f"*** Map: {eval_config.map_name}, special zones: {eval_config.zones_name_casual}")

            for num_round in range(eval_config.nb_rounds):
                gc.collect()
                result = self.one_round(eval_config, num_round + 1, hide_solution_output)
                (percent_drones_destroyed, mean_drones_health, elapsed_timestep,
                 full_rescue_timestep, score_exploration, rescued_number,
                 score_health_returned, elapsed_walltime,
                 is_max_walltime_limit_reached, has_crashed) = result

                result_score = self.score_manager.compute_score(rescued_number,
                                                                score_exploration,
                                                                score_health_returned,
                                                                full_rescue_timestep)
                (round_score, percent_rescued, score_timestep) = result_score

                mean_drones_health_percent = mean_drones_health / DRONE_INITIAL_HEALTH * 100.

                print(
                    f"\t* Round n°{num_round + 1}/{eval_config.nb_rounds}: "
                    f"\n\t\trescued nb: {int(rescued_number)}/{self.number_wounded_persons}, "
                    f"explor. score: {score_exploration:.1f}%, "
                    f"health return score: {score_health_returned:.1f}%, "
                    f"walltime elapsed: {elapsed_walltime:.0f}s/{self.max_walltime_limit}s, "
                    f"elapse timestep: {elapsed_timestep}/{self.max_timestep_limit} steps, "
                    f"time to rescue all: {full_rescue_timestep} steps."
                    f"\n\t\tpercentage of drones destroyed: {percent_drones_destroyed:.1f} %, "
                    f"mean percentage of drones health : {mean_drones_health_percent:.1f} %."
                    f"\n\t\tround score: {round_score:.1f}%, "
                    f"frequency: {elapsed_timestep / elapsed_walltime:.2f} steps/s.")
                if is_max_walltime_limit_reached:
                    print(f"\t\tThe max walltime limit of {self.max_walltime_limit}s is reached first.")

                self.data_saver.save_one_round(eval_config,
                                               num_round + 1,
                                               percent_drones_destroyed,
                                               mean_drones_health_percent,
                                               percent_rescued,
                                               score_exploration,
                                               score_health_returned,
                                               elapsed_timestep,
                                               elapsed_walltime,
                                               full_rescue_timestep,
                                               score_timestep,
                                               round_score)

                if has_crashed:
                    print(f"\t* WARNING, this program have crashed !")
                    ok = False
                    if stop_at_first_crash:
                        self.data_saver.generate_pdf_report()
                        return ok

        self.data_saver.generate_pdf_report()

        return ok


if __name__ == "__main__":
    gc.disable()
    parser = argparse.ArgumentParser(description="Launcher of a swarm-rescue simulator for the competition")
    parser.add_argument("--stop_at_first_crash", "-s", action="store_true", help="Stop the code at first crash")
    parser.add_argument("--hide_solution_output", "-o", action="store_true", help="Hide print output of the solution")
    args = parser.parse_args()

    launcher = Launcher()
    ok = launcher.go(stop_at_first_crash=args.stop_at_first_crash,
                     hide_solution_output=args.hide_solution_output)
    if not ok:
        exit(1)
