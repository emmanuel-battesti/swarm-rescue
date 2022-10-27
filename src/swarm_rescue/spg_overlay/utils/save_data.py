import csv
import os
from cv2 import cv2 as cv2
from datetime import datetime
from pathlib2 import Path

from spg_overlay.entities.sensor_disablers import EnvironmentType
from spg_overlay.utils.write_pdf import WritePdf


class SaveData:
    def __init__(self, team_info, disabled=False):
        self._disabled = disabled

        if self._disabled:
            return

        self._team_info = team_info
        self._team_number_str = str(self._team_info.team_number).zfill(2)
        date = datetime.now()
        self._directory = str(Path.home()) + '/results_swarm_rescue'
        self._path = self._directory + '/team{}_{}'.format(self._team_number_str, date.strftime("%y%m%d_%Hh%Mmin%Ss"))

        try:
            os.makedirs(self._directory, exist_ok=True)
        except FileExistsError as error:
            print(error)

        try:
            os.makedirs(self._path)
        except FileExistsError as error:
            print(error)

        self.filename = self._path + "/stats_eq{}".format(self._team_number_str) + ".csv"
        file = open(self.filename, 'w')
        file.close()
        if os.path.getsize(self.filename) == 0:
            self._add_line([('Group', 'Environment', 'Round', 'Rescued Percent', 'Exploration Score',
                             'Elapsed Time Step', 'Rescue All Time step', 'Time Score', 'Final Score')])

        self._my_pdf = WritePdf(self._team_info, self._path)

    def fill_pdf(self):
        if self._disabled:
            return

        self._my_pdf.generate_pdf()

    def _add_line(self, data):
        file = open(self.filename, 'a')
        obj = csv.writer(file)
        for element in data:
            obj.writerow(element)
        file.close()

    def save_one_round(self,
                       environment_type: EnvironmentType,
                       i_try,
                       percent_rescued,
                       score_exploration,
                       elapsed_time_step,
                       rescued_all_time_step,
                       score_time_step,
                       final_score):
        if self._disabled:
            return
        data = [(self._team_info.team_number,
                 str(environment_type.name.lower()),
                 str(i_try),
                 str(percent_rescued),
                 "%.2f" % score_exploration,
                 str(elapsed_time_step),
                 str(rescued_all_time_step),
                 str(score_time_step),
                 "%.2f" % final_score)]

        self._add_line(data)

    def save_images(self, im, im_explo_lines, im_explo_zones, environment_type, num_round):
        if self._disabled:
            return
        num_round_str = str(num_round)
        envir_str = environment_type.name.lower()
        filename = self._path + "/screen_{}_rd{}_eq{}.png".format(envir_str, num_round_str, self._team_number_str)
        im_norm = cv2.normalize(src=im, dst=None, alpha=0, beta=255,
                                norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        cv2.imwrite(filename, im_norm)

        # Save the screen capture of the explored zone done by all drones
        filename_explo = self._path + "/screen_explo_{}_rd{}_eq{}.png".format(envir_str, num_round_str,
                                                                              self._team_number_str)
        cv2.imwrite(filename_explo, im_explo_zones)

        # Save the screen capture of the path done by each drone
        filename_path = self._path + "/screen_path_{}_rd{}_eq{}.png".format(envir_str, num_round_str,
                                                                            self._team_number_str)
        cv2.imwrite(filename_path, im_explo_lines)

    @property
    def disabled(self):
        return self._disabled

    @property
    def path(self):
        return self._path
