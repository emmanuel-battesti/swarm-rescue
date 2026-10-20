import os
from pathlib import Path

from swarm_rescue.simulation.reporting.evaluation_pdf_report import EvaluationPdfReport
from swarm_rescue.simulation.reporting.stats_computation import StatsComputation
from swarm_rescue.simulation.reporting.team_info import TeamInfo
from swarm_rescue.simulation.reporting.data_website_writer import DataWebsiteWriter


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
    except Exception as error:
        print(f"Warning: could not create or access directory '{directory}': {error}")
        return

    try:
        # create the per-team path, but avoid race conditions and be tolerant
        os.makedirs(path, exist_ok=True)
    except Exception as error:
        print(f"Warning: could not create or access path '{path}': {error}")
        return

    # Instantiate and run StatsComputation in a try/except to avoid crash
    try:
        stats_computation = StatsComputation(team_info, path)
        print("**** stats_computation.process()")
        stats_computation.process()
    except FileNotFoundError as e:
        print(f"Warning: required file not found for StatsComputation in '{path}': {e}")
        return
    except Exception as e:
        print(f"Warning: failed to compute stats for path '{path}': {e}")
        return

    pdf_report = EvaluationPdfReport(team_info, path)
    print("**** pdf_report.generate_pdf()")
    try:
        pdf_report.generate_pdf(stats_computation)
    except Exception as e:
        print(f"Warning: failed to generate PDF report: {e}")
        # continue to attempt to write/print data_website

    # Write and print data_website.txt using the dedicated writer
    try:
        out = DataWebsiteWriter.write(stats_computation, team_info, result_path=path)
        print(f"data_website written to: {out}")
    except Exception as e:
        print(f"Warning: failed to write data_website.txt: {e}")

    try:
        DataWebsiteWriter.print_data(stats_computation, team_info)
    except Exception as e:
        print(f"Warning: failed to print data_website: {e}")


if __name__ == "__main__":
    manual_pdf_generation()
