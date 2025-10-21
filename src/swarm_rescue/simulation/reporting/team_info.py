from __future__ import annotations

import os

import yaml


class TeamInfo:
    """
    Parses and stores team information from a YAML file.

    Attributes:
        team_number (int): Team number.
        team_number_str_padded (str): Team number as zero-padded string.
        team_name (str): Team name.
        team_members (str): Team members.
    """

    def __init__(self):
        """
        Initialize TeamInfo by loading from YAML file.
        """
        yml_file_name = 'team_info.yml'

        with open(os.path.join(os.path.dirname(__file__), '../..', 'solutions',
                               yml_file_name), 'r') as yaml_file:
            config = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.team_number = int(config.get("team_number"))
        self.team_number_str = str(self.team_number)
        self.team_number_str_padded = str(self.team_number).zfill(3)
        self.team_name = str(config.get("team_name"))
        self.team_members = str(config.get("team_members"))
        print("The team '{}' n°{}, with {}".format(self.team_name,
                                                   self.team_number,
                                                   self.team_members))