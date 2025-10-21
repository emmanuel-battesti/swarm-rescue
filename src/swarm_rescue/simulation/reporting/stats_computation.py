import pandas
from pandas import DataFrame

from swarm_rescue.simulation.reporting.team_info import TeamInfo


class StatsComputation:
    """
    Computes and aggregates statistics from simulation results.

    Attributes:
        final_score (float): Final weighted score.
        mean_computation_freq (float): Mean computation frequency.
        mean_drones_health_percent (float): Mean drone health percent.
        percent_drones_destroyed (float): Percent of drones destroyed.
        df_configs (DataFrame): DataFrame of unique configurations.
        df_detailed (DataFrame): DataFrame of detailed stats.
        df_summary (DataFrame): DataFrame of summary stats.
        df_graph_scores (DataFrame): DataFrame for graphing scores.
        df_screenshots (DataFrame): DataFrame for screenshots.
        df_data_website (DataFrame): DataFrame for website data.
        dataframe (DataFrame): Raw loaded data.
    """

    def __init__(self, team_info: TeamInfo, result_path: str):
        """
        Initialize StatsComputation.

        Args:
            team_info (TeamInfo): Team information.
            result_path (str): Path to results.
        """
        self._team_info = team_info
        self._result_path = result_path

        self.final_score = 0
        self.mean_computation_freq = 0
        self.mean_drones_health_percent = 0
        self.percent_drones_destroyed = 0
        self.df_configs = None
        self.df_detailed = None
        self.df_summary = None
        self.df_graph_scores = None
        self.df_screenshots = None
        self.df_data_website = None

        file = pandas.read_csv(self._result_path +
                               f'/team{self._team_info.team_number_str_padded}'
                               f'_stats.csv')

        self.dataframe: DataFrame = file.copy()

    def _compute_final_score(self) -> None:
        """
        Compute the final weighted score.
        """
        id_configs = self.dataframe["Id Config"].unique()
        df_filtered = self.dataframe.loc[
            self.dataframe["Id Config"].isin(id_configs)]
        sum_score = (df_filtered["Round Score"] *
                     df_filtered["Config Weight"]).sum()
        sum_weight = df_filtered["Config Weight"].sum()
        self.final_score = sum_score / sum_weight
        # print("self.final_score", self.final_score)

    def _compute_mean_computation_freq(self) -> None:
        """
        Compute the mean computation frequency.
        """
        df_freq = (self.dataframe["Elapsed Time Step"]
                   / self.dataframe["Real Time Elapsed"])
        self.mean_computation_freq = df_freq.mean()

    def _compute_drones_health(self) -> None:
        """
        Compute mean drone health percent and percent destroyed.
        """
        self.mean_drones_health_percent = (
            self.dataframe["Mean Health Percent"].mean())
        self.percent_drones_destroyed = (
            self.dataframe["Percent Drones Destroyed"].mean())

    def _compute_dataframe_configurations(self) -> None:
        """
        Compute and store unique configurations from the input data frame.
        """
        self.df_configs = self.dataframe[["Id Config", "Map", "Zones Casual",
                                          "Config Weight", "Nb of Rounds"]].drop_duplicates()

    def _compute_dataframe_detailed_stats(self) -> None:
        """
        Compute and format detailed statistics for each round.
        """
        df = self.dataframe[
            ["Id Config", "Round", "Rescued Percent",
             "Exploration Score", "Health Return Score",
             "Time Score", "Round Score"]]
        self.df_detailed = df.rename(columns={'Id Config': 'Config n°',
                                              'Round': 'Round n°',
                                              'Rescued Percent': 'Rescued Sc.',
                                              'Exploration Score': 'Explo Score',
                                              'Health Return Score': 'Return Score'},
                                     copy=True)

        self.df_detailed["Rescued Sc."] = (
            self.df_detailed["Rescued Sc."].apply(lambda x: f"{x:.1f} %"))
        self.df_detailed["Explo Score"] = (
            self.df_detailed["Explo Score"].apply(lambda x: f"{x:.1f} %"))
        self.df_detailed["Return Score"] = (
            self.df_detailed["Return Score"].apply(lambda x: f"{x:.1f} %"))
        self.df_detailed["Time Score"] = (
            self.df_detailed["Time Score"].apply(lambda x: f"{x:.1f} %"))
        self.df_detailed["Round Score"] = (
            self.df_detailed["Round Score"].apply(lambda x: f"{x:.1f} %"))

        # print(self.df_detailed.to_string())

    def _compute_dataframe_summary_stats(self) -> None:
        """
        Compute and format summary statistics for each configuration.
        """
        df = self.dataframe[["Id Config", "Config Weight", "Round Score"]]
        df2 = df.groupby('Id Config').mean()
        df2 = df2.reset_index()

        self.df_summary = df2.rename(columns={'Id Config': 'Config n°',
                                              'Round Score': 'Config Score'},
                                     copy=True)
        self.df_summary["Config Score"] = (
            self.df_summary["Config Score"].apply(lambda x: f"{x:.1f} %"))

    def _compute_dataframe_graph_scores(self) -> None:
        """
        Compute mean scores for graphing.
        """
        df = self.dataframe[
            ["Id Config", "Rescued Percent", "Exploration Score",
             "Health Return Score", "Elapsed Time Step",
             "Rescue All Time Step", "Time Score", "Round Score"]]
        self.df_graph_scores = df.groupby('Id Config').mean()

    def _compute_dataframe_screenshots(self) -> None:
        """
        Compute the best round for screenshots for each configuration.
        """
        df = self.dataframe[["Id Config", "Map", "Zones", "Zones Casual",
                             "Config Weight", "Round", "Nb of Rounds",
                             "Percent Drones Destroyed",
                             "Mean Health Percent", "Elapsed Time Step",
                             "Real Time Elapsed", "Round Score"]]
        # Return index of the max round score for each group of "Id Config"
        index_best = df.groupby("Id Config")["Round Score"].idxmax()
        self.df_screenshots = df.loc[index_best]

        # print(self.df_screenshots.to_string())

    def _compute_dataframe_data_website(self) -> None:
        """
        Compute and format data for website display.
        """
        df = self.dataframe[
            ["Zones Casual", "Rescued Percent",
             "Exploration Score", "Health Return Score", "Time Score",
             "Mean Health Percent", "Crashed", "Round Score"]]
        df2 = df.groupby('Zones Casual').mean()
        df2 = df2.reset_index()

        self.df_data_website = df2.rename(
            columns={'Zones Casual': 'Configuration',
                     'Round Score': 'Config Score'},
            copy=True)
        self.df_data_website["Rescued Percent"] = (
            self.df_data_website["Rescued Percent"].apply(lambda x: f"{x:.0f}"))
        self.df_data_website["Exploration Score"] = (
            self.df_data_website["Exploration Score"].apply(
                lambda x: f"{x:.0f}"))
        self.df_data_website["Health Return Score"] = (
            self.df_data_website["Health Return Score"].apply(
                lambda x: f"{x:.0f}"))
        self.df_data_website["Time Score"] = (
            self.df_data_website["Time Score"].apply(lambda x: f"{x:.0f}"))
        self.df_data_website["Mean Health Percent"] = (
            self.df_data_website["Mean Health Percent"].apply(
                lambda x: f"{x:.0f}"))
        self.df_data_website["Crashed"] = (
            self.df_data_website["Crashed"].apply(lambda x: f"{x:.0f}"))
        self.df_data_website["Config Score"] = (
            self.df_data_website["Config Score"].apply(lambda x: f"{x:.2f}"))

    def process(self) -> None:
        """
        Run all computations and aggregate statistics.
        """
        self._compute_final_score()
        self._compute_mean_computation_freq()
        self._compute_drones_health()
        self._compute_dataframe_configurations()
        self._compute_dataframe_detailed_stats()
        self._compute_dataframe_summary_stats()
        self._compute_dataframe_graph_scores()
        self._compute_dataframe_screenshots()

        self._compute_dataframe_data_website()
