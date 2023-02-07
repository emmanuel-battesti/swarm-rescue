from fpdf import FPDF
import pandas
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


class MyFPDF(FPDF):
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


class WritePdf:
    def __init__(self, team_info, path):
        self.team_info = team_info
        self.team_number_str = str(self.team_info.team_number).zfill(2)
        self.path = path
        self.environment_names = ['easy', 'no_com_zone', 'no_gps_zone', 'kill_zone']

        self.pdf = MyFPDF('P', 'mm', 'A4')
        self.pdf.alias_nb_pages()
        self.pdf.add_page()
        self.pdf.set_margins(left=25, top=25, right=25)
        self.data = []
        self.data_displayed = []

        self.final_score = 0
        self.list_df_zone = []

        self.th = None
        # Effective page width, or just epw
        self.epw = self.pdf.w - 2 * self.pdf.l_margin

    def _body_text_font(self, style=''):
        self.pdf.set_font(family='Arial', style=style, size=11)

    def _header_1_font(self):
        self.pdf.set_font(family='Arial', style='B', size=15)

    def _title_font(self):
        self.pdf.set_font(family='Arial', style='B', size=18)

    def _courier_font(self, style=''):
        self.pdf.set_font(family='Courier', style=style, size=10)

    def _empty_line(self, height):
        self.pdf.ln(height * self.th)

    def _header(self):
        date = datetime.now()

        # Title
        self._title_font()
        self.th = self.pdf.font_size
        self.pdf.cell(80, ln=1)
        self.pdf.cell(0, txt="Swarm Rescue Challenge", align='C')
        self._empty_line(1.5)
        self.pdf.cell(0, txt="Evaluation Report", align='C')

        # Subtitle
        self._body_text_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Generated on " + date.strftime("%d/%m/%Y - %H:%M"), align='C')
        self._empty_line(1)

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="The team")

        # Text
        self._body_text_font(style='B')
        self._empty_line(1.5)
        self.pdf.cell(0, txt='Team n°' + self.team_number_str + ': ' + self.team_info.team_name,
                      align='L')
        self._empty_line(1)
        self.pdf.cell(0, txt='Members: ' + self.team_info.team_members, align='L')

    def _compute_data(self):
        file = pandas.read_csv(self.path + '/stats_team_{}.csv'.format(self.team_number_str))
        df = pandas.DataFrame(file)

        for column in df.columns:
            try:
                if column != "Environment":
                    df[column] = df[column].astype(float)
            except ValueError:
                print("Warning: check the name of the column in the csv file. One should be \"Environment\" !!")
                raise

        # Create df by zone
        for env_name in self.environment_names:
            self.list_df_zone.append(df.loc[df["Environment"] == env_name])

        # print("************************")
        # print(self.list_df_zone)

        # Create data that can be used by fpdf
        i = 0
        final_scores = []
        self.data.append(['Environnement', 'Rescue Sc.', 'Exploration Sc.', 'Time Sc.', 'Total Score'])
        self.data_displayed.append(True)
        # total_score_weight = 0
        for df in self.list_df_zone:
            if df.empty is False:
                final_scores.append(df["Final Score"].mean())
                self.data.append(
                    [self.environment_names[i], df["Rescued Percent"].mean(), df["Exploration Score"].mean(),
                     df["Time Score"].mean(), df["Final Score"].mean()])
                self.data_displayed.append(True)
                # if self.environment_names[i] == "easy":
                #     total_score_weight += 3
                # else:
                #     total_score_weight += 1

            else:
                final_scores.append(0)
                self.data.append([self.environment_names[i], 0, 0, 0, 0])
                self.data_displayed.append(False)
            i += 1

        total_score_weight = 6
        self.final_score = (3 * final_scores[0] + final_scores[1] + final_scores[2] + final_scores[
            3]) / total_score_weight

    def _add_table(self):
        col_width = self.epw / 5

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Final score: %.1f / 100" % self.final_score)

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Calculation of the score")

        # Text
        self._body_text_font()
        self._empty_line(1.5)
        self.pdf.cell(0, txt="In this table, you will find the average score for each environment.")
        self._empty_line(1)

        self._body_text_font()
        self.pdf.multi_cell(w=self.epw, h=1 * self.th, txt="For each round, different scores are calculated:")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Srescue, the score of rescues. This is the proportion of injured people returned to the rescue station,")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Sexpl, the exploration score. It depends on the size of the space explored by the drones,")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Stime, the score related to the time taken to explore everything and find all the injured. It is the proportion of time left in relation to the time limit.")
        self._empty_line(1)
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="A score Sr is calculated for each round with this formula:")
        self._courier_font(style='B')
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Sr = (0.7 * Srescue + 0.2 * Sexpl + 0.1 * Stime)*100")

        self._body_text_font()
        self._empty_line(1)
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Then, for each environment, several rounds are averaged.")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="The final score is calculated with this formula:")
        self._courier_font(style='B')
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Final Score = (3 * Score 'Easy' + Score 'No com zone' + Score 'No GPS zone' + Score 'Kill zone')/6")
        # ")

        self._empty_line(0.5)

        self._courier_font()

        for id_row, row in enumerate(self.data):
            if not self.data_displayed[id_row]:
                continue
            for datum in row:
                if type(datum) != str:
                    datum = "%.1f" % datum
                    datum = str(datum)

                self.pdf.cell(w=col_width, h=self.th, txt=datum, border=1)

            self._empty_line(1)

    def _add_histo(self):
        y_sauv, y_explo, y_temps, y_score = [], [], [], []
        legend = ['Rescues', 'Exploration', 'Remaining time', 'Score Total']
        # We use a min value not null for display purpose
        min_val_display = 1.0
        for i in range(1, len(self.data)):
            y_sauv.append(max(self.data[i][1], min_val_display))
            y_explo.append(max(self.data[i][2], min_val_display))
            y_temps.append(max(self.data[i][3], min_val_display))
            y_score.append(max(self.data[i][4], min_val_display))

        width = 0.10  # thickness of each bar
        dist = 0.12  # distance between the centers of the bars
        pos = np.arange(len(self.environment_names))
        y_scale = np.arange(0, 110, 10)
        # Creation of the bar chart
        plt.bar(pos - 1.5 * dist, y_sauv, width, color='firebrick')
        plt.bar(pos - 0.5 * dist, y_explo, width, color='steelblue')
        plt.bar(pos + 0.5 * dist, y_temps, width, color='darkolivegreen')
        plt.bar(pos + 1.5 * dist + 0.06, y_score, width + 0.12, color='goldenrod')
        plt.xticks(pos, self.environment_names)
        plt.yticks(y_scale)
        plt.ylabel('Success rate')
        plt.xlabel('Environment')
        plt.legend(legend, loc=1)
        filename_histo = self.path + '/histo_performance_team{}.png'.format(self.team_number_str)
        plt.savefig(filename_histo, format='png')

        self.pdf.add_page()
        # Header 1
        self._header_1_font()
        self.pdf.cell(0, txt="Graphic illustration of the scores")
        self._empty_line(1)

        self.pdf.image(name=filename_histo, w=self.epw)

    def _add_screen(self):
        for i in range(len(self.environment_names)):
            df = self.list_df_zone[i]
            if not df.empty:
                self.pdf.add_page()
                self._header_1_font()
                self.pdf.cell(0,
                              txt="Simulation details with the environment '{}'".format(self.environment_names[i]))

                self._empty_line(2)

                max_final_score = max(df["Final Score"])
                ligne_best_rd = df.loc[df["Final Score"] == max_final_score].iloc[[0]]
                best_rd = int(ligne_best_rd["Round"])

                envir_name_str = str(self.environment_names[i])
                best_rd_str = str(best_rd)

                self._body_text_font(style='B')
                self.pdf.cell(0, txt="Best round: n°{}".format(best_rd_str))
                self._empty_line(1)
                self._body_text_font()
                self.pdf.cell(0, txt="Last image of the simulation:")

                self._empty_line(0.5)
                filename_last_img = self.path + "/screen_{}_rd{}_team{}.png".format(envir_name_str,
                                                                                    best_rd_str,
                                                                                    self.team_number_str)
                self.pdf.image(filename_last_img, w=self.epw)
                self._empty_line(1)

                self.pdf.cell(0, txt="Exploration map: ")

                self._empty_line(0.5)
                filename_explo = self.path + "/screen_explo_{}_rd{}_team{}.png".format(envir_name_str,
                                                                                       best_rd_str,
                                                                                       self.team_number_str)
                self.pdf.image(filename_explo, w=self.epw)
                self._empty_line(1)

                self.pdf.cell(0, txt="Map of drone routes: ")

                self._empty_line(0.5)
                filename_routes = self.path + "/screen_path_{}_rd{}_team{}.png".format(envir_name_str,
                                                                                       best_rd_str,
                                                                                       self.team_number_str)
                self.pdf.image(filename_routes, w=self.epw)
                self._empty_line(1)

    def generate_pdf(self):
        self._compute_data()
        self._header()
        self._add_table()
        self._add_histo()
        self._add_screen()
        filename_pdf = self.path + '/report_team{}.pdf'.format(self.team_number_str)
        self.pdf.output(filename_pdf, 'F')
        print("")
        print("A new evaluation report is available here: {}".format(filename_pdf))
