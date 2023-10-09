from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

from spg_overlay.utils.constants import DRONE_INITIAL_HEALTH
from spg_overlay.reporting.stats_computation import StatsComputation


class MyFPDF(FPDF):

    def __init__(self, date_str: str = "", team_number_str: str = "", **kwargs):
        super().__init__(**kwargs)
        self.date_str = date_str
        self.team_number_str = team_number_str

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        txt = f"Team n°{self.team_number_str} - {self.date_str}  -  Page {self.page_no()}/{{nb}}"
        self.cell(w=0, h=10, txt=txt, border=0, ln=0, align='C')

    def cell(self, w=0, h=0, txt='', border=0, ln=0, align='', fill=0, link=''):
        return super().cell(w=w, h=h, txt=txt, border=border, ln=ln, align=align, fill=fill, link=link)


class EvaluationPdfReport:
    def __init__(self, team_info, path):
        self.team_info = team_info
        self.team_number_str = str(self.team_info.team_number).zfill(2)
        self.path = path
        self.stats_computation = None

        date = datetime.now()
        self.date_str = date.strftime("%d/%m/%Y - %H:%M")

        self.pdf = MyFPDF(date_str=self.date_str, team_number_str=self.team_number_str,
                          orientation='P', unit='mm', format='A4')
        self.pdf.alias_nb_pages()
        self.pdf.add_page()
        self.pdf.set_margins(left=20, top=20, right=20)

        self.th = None
        # Effective page width, or just epw
        self.epw = self.pdf.w - 2 * self.pdf.l_margin

    def _body_text_font(self, style=''):
        self.pdf.set_font(family='Arial', style=style, size=11)

    def _table_text_font(self, style=''):
        self.pdf.set_font(family='Arial', style=style, size=10)

    def _score_text_font(self):
        self.pdf.set_font(family='Arial', style='U', size=13)

    def _header_1_font(self):
        self.pdf.set_font(family='Times', style='B', size=20)

    def _title_font(self):
        self.pdf.set_font(family='Times', style='B', size=24)

    def _courier_font(self, style=''):
        self.pdf.set_font(family='Courier', style=style, size=10)

    def _empty_line(self, height):
        self.pdf.ln(height * self.th)

    def _center_image(self, img_filename, offset_from_left_margin):
        self.pdf.image(name=img_filename,
                       x=self.pdf.l_margin + offset_from_left_margin,
                       w=self.epw - 2 * offset_from_left_margin)

    def _header(self):
        # Title
        self._title_font()
        self.th = self.pdf.font_size
        self.pdf.cell(w=80, ln=1)
        self.pdf.cell(txt="Swarm Rescue Challenge", align='C')
        self._empty_line(height=1)
        self.pdf.cell(txt="Evaluation Report", align='C')

        # Subtitle "Generated on "
        self._body_text_font()
        self._empty_line(height=1)
        self.pdf.cell(txt="Generated on " + self.date_str, align='C')

        # Header Team
        self._empty_line(height=1.5)
        self._header_1_font()
        self.pdf.cell(txt=f'Team n°{self.team_number_str}: {self.team_info.team_name}', align='L')

        # Text Members
        self._body_text_font(style='')
        self._empty_line(height=1)
        self.pdf.cell(txt=f'Members: {self.team_info.team_members}', align='L')

        # Score
        self._score_text_font()
        self._empty_line(height=1)
        self.pdf.cell(txt="Final score: %.1f / 100" % self.stats_computation.final_score)

    def _add_explanation(self):

        # Header 1
        self._header_1_font()
        self._empty_line(height=1.5)
        self.pdf.cell(txt="Calculation of the score")
        self._empty_line(height=1)

        # Text
        text_list = [
            "For each round, different scores are calculated:",
            "  - Srescue, the score of rescues. This is the injured return proportion to the rescue station,",
            "  - Sexpl, the exploration score. It depends on the size of the space explored by the drones,",
            "  - Stime is the ratio of remaining time to the time limit, reflecting exploration efficiency and injured discovery.",
            "",
            "A \"round score\" Sr is calculated for each round with this formula:",
            "Sr = (0.6 * Srescue + 0.2 * Sexpl + 0.2 * Stime)*100",
            "Then, each configuration (map + zones) averages multiple rounds to generate a 'config score.'",
            "",
            "Finally, a final score is calculated as the weighted average of the config scores.",
        ]

        self._body_text_font()
        for text in text_list:
            self.pdf.multi_cell(w=self.epw, h=0.6 * self.th, txt=text)

    def _add_description_config(self):
        # Header 1
        self._header_1_font()
        self._empty_line(height=1)
        self.pdf.cell(txt="Description of the configurations")
        self._empty_line(height=1)

        self._body_text_font()

        df_configs = self.stats_computation.df_configs
        for index, row in df_configs.iterrows():
            id_config = row["Id Config"]
            map_name = row["Map"]
            zones_name_casual = row["Zones Casual"]
            weight = float(row["Config Weight"])
            nb_round = row["Nb of Rounds"]

            text_list = [
                f"Configuration n°{id_config}: ",
                f"   - map: {map_name}",
                f"   - special zones: {zones_name_casual}",
                f"   - number of rounds: {nb_round}",
                f"   - weight for final score: {weight:.1f}",
            ]

            self._body_text_font()
            for text in text_list:
                self.pdf.multi_cell(w=self.epw, h=0.6 * self.th, txt=text)

    def _add_table_detailed_stats(self):
        self.pdf.add_page()
        # Header 1
        self._header_1_font()
        self.pdf.cell(txt="Detailed statistics")
        self._empty_line(height=1)

        text_list = [
            "In this table below, you will find the score for each configuration and round.",
        ]

        self._body_text_font()
        for text in text_list:
            self.pdf.multi_cell(w=self.epw, h=0.6 * self.th, txt=text)

        self._empty_line(height=0.5)

        # column width for a 5-columns table (double column for the first one)
        col_width = self.epw / 5.5

        df_detailed = self.stats_computation.df_detailed

        self._table_text_font()
        x = self.pdf.get_x()
        y = self.pdf.get_y()
        for index, col_name in enumerate(df_detailed.columns):
            self.pdf.set_xy(x, y)
            if index == 0:
                self.pdf.multi_cell(w=0.5 * col_width, h=0.8*self.th, txt=col_name, border=1, align='C')
                x += 0.5 * col_width
            else:
                self.pdf.multi_cell(w=col_width, h=0.8*self.th, txt=col_name, border=1, align='C')
                x += col_width

        for row in df_detailed.itertuples():
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            for index_col, value in enumerate(row):
                self.pdf.set_xy(x, y)
                if index_col == 0:  # index
                    continue

                if index_col == 1:
                    self.pdf.multi_cell(w=0.5 * col_width, h=0.7*self.th, txt=str(value), border=1, align='C')
                    x += 0.5 * col_width
                else:
                    self.pdf.multi_cell(w=col_width, h=0.7*self.th, txt=str(value), border=1, align='C')
                    x += col_width

    def _add_perf_freq_health(self):
        text_list = [
            f"Average computation frequency over all rounds: {self.stats_computation.mean_computation_freq:.1f} steps/s.",
            f"Percentage of drones destroyed in collisions over of all rounds: "
            f"{self.stats_computation.percent_drones_destroyed:.1f} %.",
            f"Average level of drone health over all rounds: {self.stats_computation.mean_drones_health:.1f}/{DRONE_INITIAL_HEALTH}.",
        ]

        self._body_text_font()
        self._empty_line(height=1)
        for text in text_list:
            self.pdf.multi_cell(w=self.epw, h=0.8 * self.th, txt=text)
    def _add_table_summary_stats(self):
        # Header 1
        self._header_1_font()
        self._empty_line(height=1)
        self.pdf.cell(txt="Summary statistics")
        self._empty_line(height=1)

        text_list = [
            "In this table below, you will find the average score, across all rounds, for each configuration.",
        ]

        self._body_text_font()
        for text in text_list:
            self.pdf.multi_cell(w=self.epw, h=0.8 * self.th, txt=text)

        self._empty_line(height=0.5)

        # column width for a 4-columns table (half column for the first one)
        col_width = self.epw / 2.5

        df_summary = self.stats_computation.df_summary

        self._table_text_font()

        x = self.pdf.get_x()
        y = self.pdf.get_y()
        for index, col_name in enumerate(df_summary.columns):
            self.pdf.set_xy(x, y)
            if index == 0:
                self.pdf.multi_cell(w=0.5 * col_width, h=0.8*self.th, txt=col_name, border=1, align='C')
                x += 0.5 * col_width
            else:
                self.pdf.multi_cell(w=col_width, h=0.8*self.th, txt=col_name, border=1, align='C')
                x += col_width

        for row in df_summary.itertuples():
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            for index_col, value in enumerate(row):
                self.pdf.set_xy(x, y)
                if index_col == 0:  # index
                    continue

                if index_col == 1:
                    self.pdf.multi_cell(w=0.5 * col_width, h=0.7*self.th, txt=str(value), border=1, align='C')
                    x += 0.5 * col_width
                else:
                    self.pdf.multi_cell(w=col_width, h=0.7*self.th, txt=str(value), border=1, align='C')
                    x += col_width

        text_list = [
            f"We can now calculate the final weighted score: {self.stats_computation.final_score:.1f} / 100",
        ]

        self._body_text_font()
        self._empty_line(height=1)
        for text in text_list:
            self.pdf.multi_cell(w=self.epw, h=0.8 * self.th, txt=text)

        self._empty_line(height=1)

    def _add_graph_score(self):

        df_graph_scores = self.stats_computation.df_graph_scores

        y_sauv, y_explo, y_temps, y_score = [], [], [], []
        legend = ['Rescues', 'Exploration', 'Remaining time', 'Config Score']
        # We use a min value not null for display purpose
        config_list = []
        min_val_display = 1.0
        for index, row in df_graph_scores.iterrows():
            y_sauv.append(max(row["Rescued Percent"], min_val_display))
            y_explo.append(max(row["Exploration Score"], min_val_display))
            y_temps.append(max(row["Time Score"], min_val_display))
            y_score.append(max(row["Round Score"], min_val_display))
            config_list.append(index)

        width = 0.10  # thickness of each bar
        dist = 0.12  # distance between the centers of the bars
        pos = np.arange(df_graph_scores.shape[0])
        y_scale = np.arange(0, 110, 10)
        # Creation of the bar chart
        plt.bar(pos - 1.5 * dist, y_sauv, width, color='firebrick')
        plt.bar(pos - 0.5 * dist, y_explo, width, color='steelblue')
        plt.bar(pos + 0.5 * dist, y_temps, width, color='darkolivegreen')
        plt.bar(pos + 1.5 * dist + 0.06, y_score, width + 0.12, color='goldenrod')
        plt.xticks(pos, config_list)
        plt.yticks(y_scale)
        plt.ylabel('Success rate')
        plt.xlabel('Config')
        plt.legend(legend, loc=1)
        filename_graph = self.path + f'/graph_performance_team{self.team_number_str}.png'
        plt.savefig(filename_graph, format='png', bbox_inches='tight', dpi=200)

        # Header 1
        self._header_1_font()
        self.pdf.cell(txt="Graphic illustration of the scores")
        self._empty_line(height=1.0)

        offset = 20
        self._center_image(img_filename=filename_graph, offset_from_left_margin=offset)

    def _add_screenshots(self):
        """
        We want to show the end images of the best rounds of each configuration.
        """
        df_screenshots = self.stats_computation.df_screenshots
        offset = 20

        for index, row in df_screenshots.iterrows():
            if not row.empty:
                id_conf = row["Id Config"]
                map_name = row["Map"]
                zones_name = row["Zones"]
                zones_name_casual = row["Zones Casual"]
                nb_round = row["Nb of Rounds"]

                self.pdf.add_page()
                self._header_1_font()
                self.pdf.multi_cell(w=0, h=7,
                                    txt=f"Simulation details with the configuration n°{id_conf}")
                self._empty_line(height=0.25)

                text_list = [
                    f"Configuration n°{id_conf}: ",
                    f"   - map: {map_name}",
                    f"   - special zones: {zones_name_casual}",
                    f"   - number of rounds: {nb_round}",
                ]

                self._body_text_font()
                for text in text_list:
                    self.pdf.multi_cell(w=self.epw, h=0.6 * self.th, txt=text)
                self._empty_line(height=0.5)

                best_rd_str = str(row["Round"])
                round_score = str(row["Round Score"])
                mean_computation_freq = row["Elapsed Time Step"] / row["Real Time Elapsed"]
                mean_drones_health = row["Mean Drones Health"]
                percent_drones_destroyed = row["Percent Drones Destroyed"]

                self._body_text_font(style='B')
                self.pdf.cell(txt=f"Best round: n°{best_rd_str}, score = {round_score} %")
                self._empty_line(height=0.7)
                self._body_text_font()
                self.pdf.cell(txt=f"Mean computation frequency = {mean_computation_freq:.1f} steps/s")
                self._empty_line(height=0.7)
                self.pdf.cell(txt=f"Percentage of drones destroyed = {percent_drones_destroyed:.1f} %")
                self._empty_line(height=0.7)
                self.pdf.cell(txt=f"Mean level of drones health = {mean_drones_health:.1f}/{DRONE_INITIAL_HEALTH}")
                self._empty_line(height=1)
                self._body_text_font()
                self.pdf.cell(txt="Last image of the simulation:")

                self._empty_line(height=0.5)
                filename_last_img = (f"{self.path}/"
                                     f"screen_{map_name}_{zones_name}_rd{best_rd_str}_team{self.team_number_str}.png")

                self._center_image(img_filename=filename_last_img, offset_from_left_margin=offset)
                self._empty_line(height=1)

                self.pdf.cell(txt="Exploration map: ")

                self._empty_line(height=0.5)
                filename_explo = (f"{self.path}/"
                                  f"screen_explo_{map_name}_{zones_name}_rd{best_rd_str}_team{self.team_number_str}.png")

                self._center_image(img_filename=filename_explo, offset_from_left_margin=offset)
                self._empty_line(height=1)

                self.pdf.cell(txt="Map of drone routes: ")

                self._empty_line(height=0.5)
                filename_routes = (f"{self.path}/"
                                   f"screen_path_{map_name}_{zones_name}_rd{best_rd_str}_team{self.team_number_str}.png")

                self._center_image(img_filename=filename_routes, offset_from_left_margin=offset)
                self._empty_line(height=1)

    def generate_pdf(self, stats_computation: StatsComputation):
        self.stats_computation = stats_computation

        if self.stats_computation is not None:
            self._header()
            self._add_explanation()
            self._add_description_config()
            self._add_table_detailed_stats()
            self._add_perf_freq_health()
            self._add_table_summary_stats()
            self._add_graph_score()
            self._add_screenshots()
            filename_pdf = self.path + f'/report_team{self.team_number_str}.pdf'
            self.pdf.output(filename_pdf, 'F')
            print("")
            print(f"A new evaluation report is available here: {filename_pdf}")
        else:
            print(f"self.stats_computation is None !!")
