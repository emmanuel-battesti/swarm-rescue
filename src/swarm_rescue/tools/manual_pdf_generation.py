import os

from pathlib2 import Path

from swarm_rescue.simulation.reporting.evaluation_pdf_report import EvaluationPdfReport
from swarm_rescue.simulation.reporting.stats_computation import StatsComputation
from swarm_rescue.simulation.reporting.team_info import TeamInfo

def manual_pdf_generation() -> None:
    """
    Generates statistics and a PDF report for the evaluation.

    Creates the necessary directories, computes statistics, and generates a PDF report.
    """
    team_info = TeamInfo()
    directory = str(Path.home()) + '/results_swarm_rescue'
    path = directory + f'/team{team_info.team_number_str_padded}_test_pdf'

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

if __name__ == "__main__":
    manual_pdf_generation()
