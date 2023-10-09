import csv
import os

import cv2
from datetime import datetime

from pathlib2 import Path

from spg_overlay.reporting.evaluation import EvalConfig
from spg_overlay.reporting.evaluation_pdf_report import EvaluationPdfReport
from spg_overlay.reporting.stats_computation import StatsComputation


class DataSaver:
    """
    The DataSaver class is responsible for saving data and generating a PDF report for a team participating in the Swarm
    Rescue Challenge.

    Example Usage
        team_info = TeamInfo(...)
        data_saver = DataSaver(team_info)
        data_saver.save_one_round(...)
        data_saver.fill_pdf()

    Main functionalities
        The DataSaver class is responsible for saving data and generating a PDF report for a team participating in
        the Swarm Rescue Challenge.
        It creates a directory to store the results and a CSV file to store the statistics for each round.
        It uses the EvaluationPdfReport class to generate a PDF report with the calculated scores.

    Attributes:
        _enabled: A boolean indicating whether the saving and PDF generation is enabled.
        _team_info: An object containing information about the team participating in the challenge.
        _team_number_str: A string representation of the team number.
        _directory: The directory path where the results are stored.
        _path: The path to the directory for the current team and timestamp.
        stats_filename: The filename of the CSV file for storing the statistics.
        _pdf_report: An instance of the EvaluationPdfReport class used for generating the PDF report.
    """

    def __init__(self, team_info, enabled=True):
        """
        Initializes the DataSaver object. It creates the directory and CSV file for storing the results. It also
        creates an instance of the EvaluationPdfReport class.
        """

        self._team_info = team_info
        self._team_number_str = str(self._team_info.team_number).zfill(2)
        date = datetime.now()
        self._directory = str(Path.home()) + '/results_swarm_rescue'
        self._path = self._directory + f'/team{self._team_number_str}_{date.strftime("%y%m%d_%Hh%Mmin%Ss")}'

        try:
            os.makedirs(self._directory, exist_ok=True)
        except FileExistsError as error:
            print(error)

        try:
            os.makedirs(self._path)
        except FileExistsError as error:
            print(error)

        self._enabled = enabled
        if not self._enabled:
            return

        self.stats_filename = self._path + f"/stats_team_{self._team_number_str}.csv"
        file = open(self.stats_filename, 'w')
        file.close()
        if os.path.getsize(self.stats_filename) == 0:
            self._add_line([('Group', 'Id Config', 'Map', 'Zones', "Zones Casual", 'Config Weight', 'Round',
                             'Nb of Rounds', 'Percent Drones Destroyed', 'Mean Drones Health', 'Rescued Percent',
                             'Exploration Score', 'Elapsed Time Step', 'Real Time Elapsed', 'Rescue All Time Step', 'Time Score',
                             'Round Score')])

    def generate_pdf_report(self):
        """Generates the PDF report using the EvaluationPdfReport object."""
        if not self._enabled:
            return

        stat_computation = StatsComputation(self._team_info, self._path)
        stat_computation.process()
        pdf_report = EvaluationPdfReport(self._team_info, self._path)
        pdf_report.generate_pdf(stat_computation)

    def _add_line(self, data):
        """Appends a line of data to the CSV file."""
        file = open(self.stats_filename, 'a')
        obj = csv.writer(file)
        for element in data:
            obj.writerow(element)
        file.close()

    def save_one_round(self,
                       eval_config: EvalConfig,
                       num_round,
                       percent_drones_destroyed,
                       mean_drones_health,
                       percent_rescued,
                       score_exploration,
                       elapsed_time_step,
                       real_time_elapsed,
                       rescued_all_time_step,
                       score_time_step,
                       final_score):
        """Saves the statistics for one round to the CSV file."""
        if not self._enabled:
            return
        data = [(self._team_info.team_number,
                 eval_config.id_config,
                 eval_config.map_name,
                 eval_config.zones_name_for_filename,
                 eval_config.zones_name_casual,
                 eval_config.config_weight,
                 str(num_round),
                 eval_config.nb_rounds,
                 "%.1f" % percent_drones_destroyed,
                 "%.1f" % mean_drones_health,
                 "%.1f" % percent_rescued,
                 "%.1f" % score_exploration,
                 str(elapsed_time_step),
                 "%.2f" % real_time_elapsed,
                 str(rescued_all_time_step),
                 "%.1f" % score_time_step,
                 "%.2f" % final_score)]

        self._add_line(data)

    def save_images(self, im, im_explo_lines, im_explo_zones, map_name: str, zones_name: str, num_round: int):
        """Saves the images of the simulation for a specific map, zones and round."""
        if not self._enabled:
            return
        num_round_str = str(num_round)
        filename = (f"{self.path}/"
                    f"screen_{map_name}_{zones_name}_rd{num_round_str}_team{self._team_number_str}.png")

        im_norm = cv2.normalize(src=im, dst=None, alpha=0, beta=255,
                                norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        cv2.imwrite(filename, im_norm)

        # Save the screen capture of the explored zone done by all drones
        filename_explo = (f"{self.path}/"
                          f"screen_explo_{map_name}_{zones_name}_rd{num_round_str}_team{self._team_number_str}.png")

        cv2.imwrite(filename_explo, im_explo_zones)

        # Save the screen capture of the path done by each drone
        filename_path = (f"{self.path}/"
                         f"screen_path_{map_name}_{zones_name}_rd{num_round_str}_team{self._team_number_str}.png")

        cv2.imwrite(filename_path, im_explo_lines)

    @property
    def enabled(self):
        return self._enabled

    @property
    def path(self):
        return self._path
