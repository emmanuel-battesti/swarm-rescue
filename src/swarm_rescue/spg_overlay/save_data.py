import csv
import os
import cv2
from datetime import datetime
from pathlib2 import Path

from spg_overlay.sensor_disablers import EnvironmentType
from spg_overlay.write_pdf import WritePdf


class SaveData:
    def __init__(self, team_info):
        self.team_info = team_info
        self.team_number_str = str(self.team_info.team_number).zfill(2)
        date = datetime.now()
        self.directory = str(Path.home()) + '/results_swarm_rescue'
        # self.path = self.directory  # For debug
        self.path = self.directory + '/team{}_{}'.format(self.team_number_str, date.strftime("%y%m%d_%Hh%Mmin%Ss"))

        try:
            os.mkdir(self.directory)
            os.mkdir(self.path)
        except:
            try:
                os.mkdir(self.path)
            except:
                pass

        self.filename = self.path + "/stats_eq{}".format(self.team_number_str) + ".csv"
        file = open(self.filename, 'w')
        file.close()
        if os.path.getsize(self.filename) == 0:
            self.add_line([('Group', 'Environment', 'Round', 'Rescued Percent', 'Exploration Score',
                            'Elapsed Time Step', 'Rescue All Time step', 'Time Score', 'Final Score')])

        self._my_pdf = WritePdf(self.team_info, self.path)

    def fill_pdf(self):
        self._my_pdf.generate_pdf()

    def add_line(self, data):
        file = open(self.filename, 'a')
        obj = csv.writer(file)
        for element in data:
            obj.writerow(element)
        file.close()

    def save_one_round(self, environment_type: EnvironmentType, i_try, percent_rescued, score_exploration,
                       elapsed_time_step,
                       rescued_all_time_step, score_time_step, final_score):
        data = [(self.team_info.team_number, str(environment_type.name.lower()), str(i_try), str(percent_rescued),
                 "%.2f" % score_exploration,
                 str(elapsed_time_step), str(rescued_all_time_step), str(score_time_step), "%.2f" % final_score)]

        self.add_line(data)

    def save_images(self, im, im_explo_lines, im_explo_zones, environment_type, num_round):
        num_round_str = str(num_round)
        envir_str = environment_type.name.lower()
        filename = self.path + "/screen_{}_rd{}_eq{}.png".format(envir_str, num_round_str, self.team_number_str)
        im_norm = cv2.normalize(src=im, dst=None, alpha=0, beta=255,
                                norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        cv2.imwrite(filename, im_norm)

        # Save the screen capture of the explored zone done by all drones
        filename_explo = self.path + "/screen_explo_{}_rd{}_eq{}.png".format(envir_str, num_round_str,
                                                                             self.team_number_str)
        cv2.imwrite(filename_explo, im_explo_zones)

        # Save the screen capture of the path done by each drone
        filename_path = self.path + "/screen_path_{}_rd{}_eq{}.png".format(envir_str, num_round_str,
                                                                           self.team_number_str)
        cv2.imwrite(filename_path, im_explo_lines)
