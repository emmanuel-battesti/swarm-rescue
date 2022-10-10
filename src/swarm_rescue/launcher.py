from spg_overlay.utils.misc_data import MiscData
from spg_overlay.utils.score_manager import ScoreManager
from spg_overlay.utils.save_data import SaveData
from spg_overlay.utils.team_info import TeamInfo
from spg_overlay.gui_map.gui_sr import GuiSR

from maps.map_intermediate_01 import MyMapIntermediate01

from solutions.my_drone_random import MyDroneRandom


class MyMap(MyMapIntermediate01):
    pass


class MyDrone(MyDroneRandom):
    pass


class Launcher:
    def __init__(self):
        self.nb_rounds = 1

        self.team_info = TeamInfo()

        # Create a map only to retrieve const data associated with the map
        # Should be improved...
        my_map = MyMap()
        self.number_drones = my_map.number_drones
        self.time_step_limit = my_map.time_step_limit
        self.real_time_limit = my_map.real_time_limit
        self.number_wounded_persons = my_map.number_wounded_persons
        self.size_area = my_map.size_area

        self.score_manager = ScoreManager(number_drones=self.number_drones,
                                          time_step_limit=self.time_step_limit,
                                          real_time_limit=self.real_time_limit,
                                          total_number_wounded_persons=self.number_wounded_persons)

        # BUILD DRONES
        self.misc_data = MiscData(size_area=self.size_area,
                                  number_drones=self.number_drones)

        self.save_data = SaveData(self.team_info, disabled=True)

        self.real_time_limit_reached = False

    def one_round(self, environment_type, num_round):
        my_map = MyMap(environment_type)

        # BUILD DRONES
        my_drones = [MyDrone(identifier=i, misc_data=self.misc_data)
                     for i in
                     range(self.number_drones)]
        my_map.set_drones(my_drones)

        playground = my_map.construct_playground()

        my_gui = GuiSR(playground=playground,
                       drones=my_drones,
                       the_map=my_map,
                       total_number_wounded_persons=self.number_wounded_persons,
                       draw_interactive=False)

        my_map.explored_map.reset()
        my_gui.run()

        score_exploration = my_map.explored_map.score()

        last_image_explo_lines = my_map.explored_map.get_pretty_map_explo_lines()
        last_image_explo_zones = my_map.explored_map.get_pretty_map_explo_zones()
        self.save_data.save_images(my_gui.last_image,
                                   last_image_explo_lines,
                                   last_image_explo_zones,
                                   environment_type,
                                   num_round)

        return my_gui.elapsed_time, my_gui.rescued_all_time_step, score_exploration, my_gui.rescued_number, my_gui.real_time_elapsed

    def go(self):
        for environment_type in MyMap.environment_series:
            print("*** Environment '{}'".format(environment_type.name.lower()))
            for i_try in range(self.nb_rounds):
                result = self.one_round(environment_type, i_try)
                (
                    elapsed_time_step, rescued_all_time_step, score_exploration, rescued_number,
                    real_time_elapsed) = result

                result_score = self.score_manager.compute_score(rescued_number,
                                                                score_exploration,
                                                                rescued_all_time_step)
                (final_score, percent_rescued, score_time_step) = result_score

                print("\t* Round n°{}".format(i_try),
                      ", real time elapsed = {:.1f}/{}s".format(
                          real_time_elapsed, self.real_time_limit),
                      ", rescued number ={}/{}".format(
                          rescued_number, self.number_wounded_persons),
                      ", exploration score =", "{:.1f}%".format(
                          score_exploration * 100),
                      ", elapse time = {}/{} steps".format(
                          elapsed_time_step, self.time_step_limit),
                      ", time to rescue all = {} steps".format(
                          rescued_all_time_step),
                      ", final score =", "{:.2f}/100".format(final_score)
                      )
                if self.real_time_limit_reached:
                    print("\t\tThe real time limit of {}s is reached first.".format(
                        self.real_time_limit))

                self.save_data.save_one_round(environment_type,
                                              i_try,
                                              percent_rescued,
                                              score_exploration,
                                              elapsed_time_step,
                                              rescued_all_time_step,
                                              score_time_step,
                                              final_score)
        self.save_data.fill_pdf()


if __name__ == "__main__":
    launcher = Launcher()
    launcher.go()
