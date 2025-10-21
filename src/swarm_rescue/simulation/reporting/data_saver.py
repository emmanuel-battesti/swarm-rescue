import csv
import os

import cv2

from swarm_rescue.simulation.reporting.evaluation import EvalConfig
from swarm_rescue.simulation.reporting.evaluation_pdf_report import EvaluationPdfReport
from swarm_rescue.simulation.reporting.stats_computation import StatsComputation
from swarm_rescue.simulation.reporting.team_info import TeamInfo


# from datetime import datetime
# from pathlib2 import Path


class DataSaver:
    """
    The DataSaver class is responsible for saving data and generating a PDF
    report for a team participating in the Swarm Rescue Challenge.

    Example Usage
        team_info = TeamInfo(...)
        data_saver = DataSaver(team_info)
        data_saver.save_one_round(...)
        data_saver.fill_pdf()

    Main functionalities
        The DataSaver class is responsible for saving data and generating a PDF
        report for a team participating in the Swarm Rescue Challenge.
        It creates a directory to store the results and a CSV file to store the
        statistics for each round.
        It uses the EvaluationPdfReport class to generate a PDF report with the
        calculated scores.

    Attributes:
        _enabled: A boolean indicating whether the saving and PDF generation is
         enabled.
        _team_info: An object containing information about the team
        participating in the challenge.
        _result_path: The path to the directory for the current team and timestamp.
        _stats_filename: The filename of the CSV file for storing the statistics.
    """

    def __init__(self, team_info: TeamInfo, result_path: str = None, enabled: bool = True):
        """
        Initializes the DataSaver object. It creates the directory and CSV file
        for storing the results. It also creates an instance of the
        EvaluationPdfReport class.

        Args:
            team_info (TeamInfo): The team information object.
            result_path (str, optional): Path to store results.
            enabled (bool): Whether saving and PDF generation is enabled.
        """
        self._team_info = team_info
        self._result_path = result_path

        self._enabled = enabled
        if not self._enabled:
            return

        self._stats_filename = None

        self._images_path = None
        if self._result_path is not None:
            try:
                self._images_path = self._result_path + "/images_pdf/"
                os.makedirs(self._images_path, exist_ok=True)
            except FileExistsError as error:
                print(error)

    def generate_pdf_report(self) -> None:
        """
        Generates the PDF report using the EvaluationPdfReport object.
        """
        if not self._enabled:
            return

        stat_computation = StatsComputation(self._team_info, self._result_path)
        stat_computation.process()
        pdf_report = EvaluationPdfReport(self._team_info, self._result_path)
        pdf_report.generate_pdf(stat_computation)

    def _create_stats_file(self) -> None:
        """
        Create the file for the result stats and add the header line.
        """
        self._stats_filename = (self._result_path +
                                f"/team{self._team_info.team_number_str_padded}"
                                f"_stats.csv")
        file = open(self._stats_filename, 'w')
        file.close()
        if os.path.getsize(self._stats_filename) == 0:
            self._add_line([('Group', 'Id Config', 'Map', 'Zones',
                             "Zones Casual", 'Config Weight', 'Round',
                             'Nb of Rounds', 'Percent Drones Destroyed',
                             'Mean Health Percent', 'Rescued Percent',
                             'Exploration Score', 'Health Return Score',
                             'Elapsed Time Step', 'Real Time Elapsed',
                             'Rescue All Time Step', 'Time Score', 'Crashed',
                             'Round Score')])

    def _add_line(self, data) -> None:
        """
        Appends a line of data to the CSV file.

        Args:
            data: List of tuples or lists to write as rows.
        """
        if self._stats_filename is None:
            self._create_stats_file()

        file = open(self._stats_filename, 'a')
        obj = csv.writer(file)
        for element in data:
            obj.writerow(element)
        file.close()

    def save_one_round(self,
                       eval_config: EvalConfig,
                       num_round: int,
                       percent_drones_destroyed: float,
                       mean_drones_health_percent: float,
                       percent_rescued: float,
                       score_exploration: float,
                       score_health_returned: float,
                       elapsed_timestep: int,
                       elapsed_walltime: float,
                       full_rescue_timestep: int,
                       score_timestep: float,
                       has_crashed: bool,
                       final_score: float) -> None:
        """
        Saves the statistics for one round to the CSV file.

        Args:
            eval_config (EvalConfig): The evaluation configuration.
            num_round (int): The round number.
            percent_drones_destroyed (float): Percentage of drones destroyed.
            mean_drones_health_percent (float): Mean health percent of drones.
            percent_rescued (float): Percentage of rescued persons.
            score_exploration (float): Exploration score.
            score_health_returned (float): Health return score.
            elapsed_timestep (int): Number of elapsed timesteps.
            elapsed_walltime (float): Elapsed wall time.
            full_rescue_timestep (int): Timestep when all rescued.
            score_timestep (float): Time score.
            has_crashed (bool): Whether the round crashed.
            final_score (float): Final score for the round.
        """
        if not self._enabled:
            return

        if has_crashed:
            crashed_value = 100.0
        else:
            crashed_value = 0.0

        data = [(self._team_info.team_number,
                 eval_config.id_config,
                 eval_config.map_name,
                 eval_config.zones_name_for_filename,
                 eval_config.zones_name_casual,
                 eval_config.config_weight,
                 str(num_round),
                 eval_config.nb_rounds,
                 "%.1f" % percent_drones_destroyed,
                 "%.1f" % mean_drones_health_percent,
                 "%.1f" % percent_rescued,
                 "%.1f" % score_exploration,
                 "%.1f" % score_health_returned,
                 str(elapsed_timestep),
                 "%.2f" % elapsed_walltime,
                 str(full_rescue_timestep),
                 "%.1f" % score_timestep,
                 crashed_value,
                 "%.2f" % final_score)]

        self._add_line(data)

    def save_images(self, im, im_explo_lines, im_explo_zones, map_name: str,
                    zones_name: str, num_round: int) -> None:
        """
        Saves the images of the simulation for a specific map, zones and round.

        Args:
            im: Main simulation image.
            im_explo_lines: Image of explored lines.
            im_explo_zones: Image of explored zones.
            map_name (str): Name of the map.
            zones_name (str): Name of the zones.
            num_round (int): Round number.
        """
        if not self._enabled:
            return
        num_round_str = str(num_round)
        filename = (f"{self._images_path}/"
                    f"team{self._team_info.team_number_str_padded}_"
                    f"{map_name}_{zones_name}_rd{num_round_str}_"
                    f"screen.png")

        im_norm = cv2.normalize(src=im, dst=None, alpha=0, beta=255,
                                norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        if im_norm is not None:
            cv2.imwrite(filename, im_norm)

        # Save the screen capture of the explored zone done by all drones
        filename_explo = (f"{self._images_path}/"
                          f"team{self._team_info.team_number_str_padded}_"
                          f"{map_name}_{zones_name}_rd{num_round_str}_"
                          f"screen_explo.png")

        if im_explo_zones is not None:
            cv2.imwrite(filename_explo, im_explo_zones)

        # Save the screen capture of the path done by each drone
        filename_path = (f"{self._images_path}/"
                         f"team{self._team_info.team_number_str_padded}_"
                         f"{map_name}_{zones_name}_rd{num_round_str}_"
                         f"screen_path.png")

        if im_explo_lines is not None:
            cv2.imwrite(filename_path, im_explo_lines)
