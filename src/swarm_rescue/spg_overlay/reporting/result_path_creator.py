import csv
import os

import cv2
from datetime import datetime

from pathlib2 import Path


class ResultPathCreator:
    """
    The ResultPathCreator class is responsible for creating a path for saving
    data
    """

    def __init__(self, team_info):
        """
        Initializes the ResultPathCreator object. It creates the directory for
        storing the results.
        """

        self._team_info = team_info
        self._directory = str(Path.home()) + '/results_swarm_rescue'
        self._result_path = None

        self._create_path_name()
        self._make_dir()

    def _create_path_name(self):
        date = datetime.now()

        # Create the folder to keep results of the mission
        self._result_path = (self._directory
                             + f'/team{self._team_info.team_number_str}'
                               f'_{date.strftime("%y%m%d_%Hh%Mmin%Ss")}')

    def _make_dir(self):
        try:
            os.makedirs(self._directory, exist_ok=True)
        except FileExistsError as error:
            print(error)

        try:
            os.makedirs(self._result_path)
        except FileExistsError as error:
            print(error)

    @property
    def path(self):
        return self._result_path
