#!/usr/bin/env python3
"""
Classe utilitaire pour écrire le fichier data_website.txt à partir d'un
objet StatsComputation.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from swarm_rescue.simulation.reporting.stats_computation import StatsComputation
from swarm_rescue.simulation.reporting.team_info import TeamInfo


class DataWebsiteWriter:
    """Écrit les données destinées au site web à partir d'un StatsComputation.

    Usage:
        DataWebsiteWriter.write(stats_computation, team_info, result_path=None, out_file=None)

    - Si out_file est fourni, on écrit dedans (append).
    - Sinon si result_path est fourni, on écrit dans result_path/data_website.txt (append).
    - Sinon on écrit dans le fichier data_website.txt relatif au module.
    """

    @staticmethod
    def _default_path() -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../data_website.txt")

    @classmethod
    def write(cls, stats_computation: StatsComputation, team_info: TeamInfo,
              result_path: Optional[str] = None, out_file: Optional[str] = None) -> str:
        """Écrit les données et retourne le chemin du fichier écrit.

        Écrit en mode append, en ajoutant les nouvelles données à la suite des
        précédentes. Crée le dossier si nécessaire.
        """
        df = stats_computation.df_data_website
        assert df is not None, "Statistics have not been computed yet."
        date_str = datetime.now().strftime("%d/%m/%Y - %H:%M")

        if out_file:
            file_path = os.path.expanduser(out_file)
        elif result_path:
            file_path = os.path.join(os.path.expanduser(result_path), "data_website.txt")
        else:
            file_path = os.path.abspath(cls._default_path())

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, "a", encoding='utf-8') as file:
                file.write(f"\nData for the website (generated on {date_str}):\n")
                for _, row in df.iterrows():
                    if not row.empty:
                        configuration = row.get("Configuration", "")
                        rescued_percent = row.get("Rescued Percent", "")
                        exploration_score = row.get("Exploration Score", "")
                        health_return_score = row.get("Health Return Score", "")
                        time_score = row.get("Time Score", "")
                        crashed_percent = row.get("Crashed", "")
                        config_score = row.get("Config Score", "")

                        # ensure strings
                        line = (f"{team_info.team_number},"
                                f'"{configuration}",'
                                f"{rescued_percent},"
                                f"{exploration_score},"
                                f"{health_return_score},"
                                f"{time_score},"
                                f"{crashed_percent}%,"
                                f"{config_score}\n")
                        file.write(line)
            print(f"The data_website file has been updated: {os.path.normpath(file_path)}")
            return file_path
        except OSError as e:
            print(f"Error writing data_website file {file_path}: {e}")
            raise

    @classmethod
    def print_data(cls, stats_computation: StatsComputation, team_info: TeamInfo) -> None:
        """Affiche sur la sortie standard les mêmes lignes que celles écrites dans le fichier.

        Usage: DataWebsiteWriter.print_data(stats_computation, team_info)
        """
        df = stats_computation.df_data_website
        assert df is not None, "Statistics have not been computed yet."
        print("\nData for the website:")
        for _, row in df.iterrows():
            if not row.empty:
                configuration = row.get("Configuration", "")
                rescued_percent = row.get("Rescued Percent", "")
                exploration_score = row.get("Exploration Score", "")
                health_return_score = row.get("Health Return Score", "")
                time_score = row.get("Time Score", "")
                # drone_health_percent = row["Mean Health Percent"]
                crashed_percent = row.get("Crashed", "")
                config_score = row.get("Config Score", "")

                print(f"{team_info.team_number},"
                      f'"{configuration}",'
                      f"{rescued_percent},"
                      f"{exploration_score},"
                      f"{health_return_score},"
                      f"{time_score},"
                      # f"{drone_health_percent},"
                      f"{crashed_percent}%,"
                      f"{config_score}")


