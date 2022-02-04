import csv
import os
import cv2
import pygame
from datetime import datetime
from time import strftime
from pathlib import Path

from spg_overlay.sensor_disablers import EnvironmentType
from spg_overlay.write_pdf import WritePdf


class SaveData:
    def __init__(self, team_info):
        self.team_info = team_info
        date = datetime.now()
        self.directory = str(Path.home()) + '/results_swarm_rescue'
        self.path = self.directory + '/team{}_{}'.format(str(self.team_info.team_number).zfill(2), date.strftime("%y%m%d_%Hh%Mmin%Ss"))

        try:
            os.mkdir(self.directory)
            os.mkdir(self.path)
        except:
            try:
                os.mkdir(self.path)
            except:
                pass

        self.filename = self.path + "/stats_eq{}".format(str(self.team_info.team_number).zfill(2)) + ".csv"
        file = open(self.filename, 'a')
        file.close()
        if os.path.getsize(self.filename) == 0:
            self.add_line([('Group', 'Environment', 'Round', 'Rescued Percent', 'Exploration Score',
                            'Elapsed Time Step', 'Time To Rescue All', 'Time Score', 'Final Score')])

        self.my_pdf = WritePdf()

    def fill_pdf(self):
        self.my_pdf.generate_pdf(self.team_info, self.path)

    def add_line(self, data):
        file = open(self.filename, 'a')
        obj = csv.writer(file)
        for element in data:
            obj.writerow(element)
        file.close()

    def save_one_round(self, environment_type: EnvironmentType, i_try, percent_rescued, score_exploration, elapsed_time_step,
                       time_rescued_all, score_time_step, final_score):
        data = [(self.team_info.team_number, str(environment_type.name.lower()), str(i_try), str(percent_rescued), "%.2f" % score_exploration,
                 str(elapsed_time_step), str(time_rescued_all), str(score_time_step), "%.2f" % final_score)]

        self.add_line(data)

    def save_images(self, im, im_explo_lines, im_explo_zones, environment_type, num_round):
        filename = self.path + "/screen_{}_rd{}_eq{}.png".format(environment_type.name.lower(), str(num_round), str(self.team_info.team_number).zfill(2))
        im_norm = cv2.normalize(src=im, dst=None, alpha=0, beta=255,
                                norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        cv2.imwrite(filename, im_norm)

        filename_explo = self.path + "/screen_explo_{}_rd{}_eq{}.png".format(environment_type.name.lower(), str(num_round),
                                                                             str(self.team_info.team_number).zfill(2))
        cv2.imwrite(filename_explo, im_explo_zones)
