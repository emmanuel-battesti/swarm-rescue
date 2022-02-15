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

        self.score_final = 0
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
        self.pdf.cell(0, txt="Challenge Intelligence Répartie", align='C')
        self._empty_line(1.5)
        self.pdf.cell(0, txt="Rapport d'évaluation", align='C')

        # Subtitle
        self._body_text_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Généré le " + date.strftime("%d/%m/%Y - %H:%M"), align='C')
        self._empty_line(1)

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="L'équipe")

        # Text
        self._body_text_font(style='B')
        self._empty_line(1.5)
        self.pdf.cell(0, txt='Equipe n°' + self.team_number_str + ' : ' + self.team_info.team_name,
                      align='L')
        self._empty_line(1)
        self.pdf.cell(0, txt='Membres : ' + self.team_info.team_members, align='L')

    def _compute_data(self):
        file = pandas.read_csv(self.path + '/stats_eq{}.csv'.format(self.team_number_str))
        df = pandas.DataFrame(file)
        # df = df.loc[df["Group"] != "Group"]

        for column in df.columns:
            try:
                df[column] = df[column].astype(float)
            except:
                pass

        list_df_zone = []
        ## create df by zone
        for env_name in self.environment_names:
            list_df_zone.append(df.loc[df["Environment"] == env_name])

        ## create data that can be used by fpdf
        i = 0
        final_scores = []
        self.data.append(['Environnement', 'Sc. Sauvetages', 'Sc. Exploration', 'Sc. Temps', 'Score Total'])
        for df in list_df_zone:
            if df.empty is False:
                final_scores.append(df["Final Score"].mean())
                self.data.append(
                    [self.environment_names[i], df["Rescued Percent"].mean(), df["Exploration Score"].mean(),
                     df["Time Score"].mean(), df["Final Score"].mean()])
            else:
                final_scores.append(0)
                self.data.append([self.environment_names[i], 0, 0, 0, 0])
            i += 1

        score_final = (3 * final_scores[0] + final_scores[1] + final_scores[2] + final_scores[3]) / 6
        return score_final, list_df_zone

    def _add_table(self):
        col_width = self.epw / 5

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Score final : %.1f / 100" % self.score_final)

        # Header 1
        self._header_1_font()
        self._empty_line(2)
        self.pdf.cell(0, txt="Calcul du score")

        # Text
        self._body_text_font()
        self._empty_line(1.5)
        self.pdf.cell(0, txt="Dans ce tableau, vous retrouvez le score moyen pour chacun des environnements.")
        self._empty_line(1)

        self._body_text_font()
        self.pdf.multi_cell(w=self.epw, h=1 * self.th, txt="Pour chaque round, différents scores sont calculés :")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Ssauv, le score de sauvetages. Il s'agit de la proportion de blessés retournés au poste de secours,")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Sexpl, le score d'exploration. Il dépend de la taille de l'espace exploré par les drones,")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="    - Stemps, le score lié au temps mis pour tout explorer et retrouver tous les blessés. Il s'agit de la proportion de temps restant par rapport au temps imparti.")
        self._empty_line(1)
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Un score Sr est calculé pour chaque round avec cette formule :")
        self._courier_font(style='B')
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Sr = (0.7 * Ssauv + 0.2 * Sexpl + 0.1 * Stemps)*100")

        self._body_text_font()
        self._empty_line(1)
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Ensuite, pour chaque environnement, on fait la moyenne de plusieurs rounds.")
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="On  calcule le score final avec cette formule:")
        self._courier_font(style='B')
        self.pdf.multi_cell(w=self.epw, h=1 * self.th,
                            txt="Score Final = (3 * Score 'Easy' + Score 'No com zone' + Score 'No GPS zone' + Score 'Kill zone')/6")
        # ")

        self._empty_line(0.5)

        self._courier_font()

        for row in self.data:
            for datum in row:
                if type(datum) != str:
                    datum = "%.2f" % datum
                    datum = str(datum)

                self.pdf.cell(w=col_width, h=self.th, txt=datum, border=1)

            self._empty_line(1)

    def _add_histo(self):
        y_sauv, y_explo, y_temps, y_score = [], [], [], []
        legend = ['Sauvetages', 'Exploration', 'Temps restant', 'Score Total']
        # We use a min value not null for display purpose
        min_val_display = 0.01
        for i in range(1, len(self.data)):
            y_sauv.append(max(self.data[i][1], min_val_display))
            y_explo.append(max(self.data[i][2], min_val_display))
            y_temps.append(max(self.data[i][3], min_val_display))
            y_score.append(max(self.data[i][4] / 100, min_val_display))

        width = 0.10  # épaisseur de chaque bâton
        dist = 0.12  # distance entre les centre des batons
        pos = np.arange(len(self.environment_names))
        y_scale = np.arange(0, 1.1, 0.1)
        # Création du diagramme en bâtons (bâtons côte à côte)
        plt.bar(pos - 1.5 * dist, y_sauv, width, color='firebrick')
        plt.bar(pos - 0.5 * dist, y_explo, width, color='steelblue')
        plt.bar(pos + 0.5 * dist, y_temps, width, color='darkolivegreen')
        plt.bar(pos + 1.5 * dist + 0.06, y_score, width + 0.12, color='goldenrod')
        plt.xticks(pos, self.environment_names)
        plt.yticks(y_scale)
        plt.ylabel('Taux de réussite')
        plt.xlabel('Environnement')
        plt.legend(legend, loc=1)
        filename = self.path + '/histo_performance_eq{}.png'.format(self.team_number_str)
        plt.savefig(filename, format='png')

        self.pdf.add_page()
        # Header 1
        self._header_1_font()
        self.pdf.cell(0, txt="Illustration graphique des scores")
        self._empty_line(1)

        self.pdf.image(name=filename, w=self.epw)

    def _add_screen(self):

        for i in range(len(self.environment_names)):
            try:
                self.pdf.add_page()
                self._header_1_font()
                self.pdf.cell(0,
                              txt="Détails de simulation avec l'environnement '{}'".format(self.environment_names[i]))

                self._empty_line(2)

                df = self.list_df_zone[i]
                max_finale_score = max(df["Final Score"])
                ligne_best_rd = df.loc[df["Final Score"] == max_finale_score]
                best_rd = int(ligne_best_rd["Round"])

                envir_name_str = str(self.environment_names[i])
                best_rd_str = str(best_rd)

                self._body_text_font(style='B')
                self.pdf.cell(0, txt="Meilleur round : n°{}".format(best_rd_str))
                self._empty_line(1)
                self._body_text_font()
                self.pdf.cell(0, txt="Dernière image de la simulation :")

                self._empty_line(0.5)
                filename = self.path + "/screen_{}_rd{}_eq{}.png".format(envir_name_str,
                                                                         best_rd_str,
                                                                         self.team_number_str)
                self.pdf.image(filename, w=self.epw)
                self._empty_line(1)

                self.pdf.cell(0, txt="Carte d'exploration : ")

                self._empty_line(0.5)
                filename = self.path + "/screen_explo_{}_rd{}_eq{}.png".format(envir_name_str,
                                                                               best_rd_str,
                                                                               self.team_number_str)
                self.pdf.image(filename, w=self.epw)
                self._empty_line(1)

                self.pdf.cell(0, txt="Carte de trajets des drones : ")

                self._empty_line(0.5)
                filename = self.path + "/screen_path_{}_rd{}_eq{}.png".format(envir_name_str,
                                                                              best_rd_str,
                                                                              self.team_number_str)
                self.pdf.image(filename, w=self.epw)
                self._empty_line(1)
            except:
                pass

    def generate_pdf(self):
        self.score_final, self.list_df_zone = self._compute_data()
        self._header()
        self._add_table()
        self._add_histo()
        self._add_screen()
        filename = self.path + '/report_team{}.pdf'.format(self.team_number_str)
        self.pdf.output(filename, 'F')
        print("A new evaluation report is available here : {}".format(filename))
