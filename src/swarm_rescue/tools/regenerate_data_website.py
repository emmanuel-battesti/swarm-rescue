#!/usr/bin/env python3
"""
Regénération de data_website.txt en utilisant la classe StatsComputation

Usage:
  python regenerate_data_website.py [--results-dir DIR] [--out-file FILE] [--no-dedupe]

Ce script parcourt récursivement le répertoire des résultats, trouve les
fichiers team*_stats.csv, crée un objet StatsComputation par équipe, appelle
process(), récupère df_data_website et écrit un fichier de sortie.

Par défaut, le fichier de sortie est ~/results_swarm_rescue/data_website.txt
"""
from __future__ import annotations

import argparse
import os
import re
from typing import List, Optional, cast

from swarm_rescue.simulation.reporting.stats_computation import StatsComputation
from swarm_rescue.simulation.reporting.data_website_writer import DataWebsiteWriter
from swarm_rescue.simulation.reporting.team_info import TeamInfo


class TeamInfoMinimal:
    """Objet minimal pour fournir team_number et team_number_str_padded à StatsComputation.

    Cette classe évite de charger le YAML ou d'exiger la structure complète de
    `TeamInfo` lors de la régénération en masse: elle fournit uniquement les
    attributs nécessaires.
    """

    def __init__(self, team_number: int):
        self.team_number = int(team_number)
        self.team_number_str = str(self.team_number)
        self.team_number_str_padded = str(self.team_number).zfill(3)


def find_stats_files(results_dir: str) -> List[str]:
    pattern = os.path.join(os.path.expanduser(results_dir), "**", "team*_stats.csv")
    import glob

    files = glob.glob(pattern, recursive=True)
    files.sort()
    return files


def infer_team_number_from_filename(path: str) -> Optional[str]:
    m = re.search(r"team(\d+)_stats\.csv", os.path.basename(path))
    if m:
        return m.group(1)
    return None


def normalize_crashed(value: str) -> str:
    v = value.strip()
    if not v:
        return ''
    if v.endswith('%'):
        return v
    # try numeric
    try:
        f = float(v.replace(',', '.'))
        if 0 <= f <= 100:
            if f.is_integer():
                return f"{int(f)}%"
            return f"{f}%"
    except Exception:
        pass
    return v


def regenerate(results_dir: str, out_file: str, dedupe: bool = True) -> None:
    results_dir_expanded = os.path.expanduser(results_dir)
    files = find_stats_files(results_dir_expanded)
    if not files:
        print(f"Aucun fichier 'team*_stats.csv' trouvé sous {results_dir_expanded}")
        return

    out_file_expanded = os.path.expanduser(out_file)
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_file_expanded), exist_ok=True)

    # Remove any existing output file so the run starts from a clean file.
    if os.path.exists(out_file_expanded):
        try:
            os.remove(out_file_expanded)
        except Exception as e:
            print(f"Warning: could not remove existing out_file {out_file_expanded}: {e}")

    processed = 0
    skipped = 0

    for f in files:
        team = infer_team_number_from_filename(f)
        if team is None:
            print(f"Impossible d'extraire le numéro d'équipe depuis le nom de fichier: {f}, saut")
            skipped += 1
            continue
        result_dir = os.path.dirname(f)

        # create a minimal TeamInfo-compatible object but cast it to TeamInfo for typing
        team_info_min = TeamInfoMinimal(int(team))
        team_info = cast(TeamInfo, team_info_min)

        try:
            sc = StatsComputation(team_info, result_dir)
            sc.process()
        except FileNotFoundError as e:
            print(f"Erreur: fichier introuvable pour l'équipe {team} dans {result_dir}: {e}")
            skipped += 1
            continue
        except Exception as e:
            print(f"Erreur lors du calcul des stats pour l'équipe {team} dans {result_dir}: {e}")
            skipped += 1
            continue

        # if there's no data to write, skip
        df = getattr(sc, 'df_data_website', None)
        if df is None or getattr(df, 'shape', (0,))[0] == 0:
            print(f"Aucune donnée website pour l'équipe {team}, saut")
            skipped += 1
            continue

        # Use DataWebsiteWriter to append the team's website data into the single out_file
        try:
            DataWebsiteWriter.write(sc, team_info, out_file=out_file_expanded)
            processed += 1
        except Exception as e:
            print(f"Erreur en écrivant les données website pour l'équipe {team}: {e}")
            skipped += 1
            continue

    print(f"Processed {processed} teams, skipped {skipped} files. Output: {out_file_expanded}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Regenerate data_website.txt')
    parser.add_argument('--results-dir', default='~/results_swarm_rescue', help='Répertoire racine contenant les résultats')
    parser.add_argument('--out-file', default='~/results_swarm_rescue/data_website.txt', help='Fichier de sortie')
    parser.add_argument('--no-dedupe', dest='dedupe', action='store_false', help='Désactiver la déduplication')
    args = parser.parse_args()

    regenerate(args.results_dir, args.out_file, dedupe=args.dedupe)


if __name__ == '__main__':
    main()
