from __future__ import annotations

import os
import yaml


class TeamInfo:
    """
        The TeamInfo class is responsible for parsing a YAML file containing team information and storing the
         data in its fields. It also prints out the team's name, number, and members.
    """

    def __init__(self):
        yml_file_name = 'team_info.yml'

        with open(os.path.join(os.path.dirname(__file__), '../..', 'solutions', yml_file_name), 'r') as yaml_file:
            config = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.team_number = int(config.get("team_number"))
        self.team_name = str(config.get("team_name"))
        self.team_members = str(config.get("team_members"))
        print("The team '{}' n°{}, with {}".format(self.team_name, self.team_number, self.team_members))
