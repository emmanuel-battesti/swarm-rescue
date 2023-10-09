import os
from pathlib2 import Path

from spg_overlay.reporting.evaluation_pdf_report import EvaluationPdfReport
from spg_overlay.reporting.stats_computation import StatsComputation
from spg_overlay.reporting.team_info import TeamInfo

team_info = TeamInfo()
team_number_str = str(team_info.team_number).zfill(2)
directory = str(Path.home()) + '/results_swarm_rescue'
path = directory + f'/team{team_number_str}_test_pdf'

try:
    os.makedirs(directory, exist_ok=True)
except FileExistsError as error:
    print(error)

try:
    os.makedirs(path)
except FileExistsError as error:
    print(error)

stats_computation = StatsComputation(team_info, path)
print("**** stats_computation.process()")
stats_computation.process()

pdf_report = EvaluationPdfReport(team_info, path)
print("**** pdf_report.generate_pdf()")
pdf_report.generate_pdf(stats_computation)
