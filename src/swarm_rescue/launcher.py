import time

from cv2 import cv2 as cv2
import numpy as np
from simple_playgrounds.engine import Engine

from spg_overlay.fps_display import FpsDisplay
from spg_overlay.misc_data import MiscData
from spg_overlay.score_manager import ScoreManager
from spg_overlay.save_data import SaveData
from spg_overlay.sensor_disablers import EnvironmentType
from spg_overlay.team_info import TeamInfo

from maps.map_lidar_communication import MyMapLidarCommunication
from maps.map_random import MyMapRandom
from maps.map_compet_01 import MyMapCompet01
from maps.map_compet_02 import MyMapCompet02

from solutions.my_drone_lidar_communication import MyDroneLidarCommunication
from solutions.my_drone_random import MyDroneRandom


class MyMap(MyMapCompet02):
    pass


class MyDrone(MyDroneLidarCommunication):
    pass


class Launcher:
    def __init__(self):
        self.display = True
        self.nb_rounds = 3
        self.with_com = True

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

        self.save_data = SaveData(self.team_info)

        self.real_time_limit_reached = False

    def define_all_messages(self, a_map):
        messages = []
        for i in range(0, self.number_drones):
            if self.with_com:
                msg_data = a_map.drones[i].define_message()
                one_message = (a_map.drones[i].communication, msg_data, None)
                messages.append(one_message)
        return messages

    def one_round(self, environment_type, num_round):
        my_map = MyMap(environment_type)

        # BUILD DRONES
        my_drones = [MyDrone(identifier=i, misc_data=self.misc_data)
                     for i in
                     range(self.number_drones)]
        my_map.set_drones(my_drones)

        engine = Engine(playground=my_map.playground, time_limit=self.time_step_limit, screen=self.display)

        # fps_display = FpsDisplay(period_display=0.5)

        rescued_number = 0
        rescued_all_time_step = 0
        my_map.explored_map.reset()

        start_real_time = time.time()

        while engine.game_on:
            # print("time=", engine.elapsed_time)
            if self.display:
                engine.update_screen()

            engine.update_observations(grasped_invisible=True)

            my_map.explored_map.update(my_drones)

            # COMPUTE ALL THE MESSAGES
            messages = self.define_all_messages(my_map)

            # COMPUTE ACTIONS
            actions = {}
            for i in range(0, self.number_drones):
                actions[my_drones[i]] = my_drones[i].control()

            my_drones[0].display()

            terminate = engine.step(actions, messages)

            # REWARDS
            new_reward = 0
            for i in range(0, self.number_drones):
                new_reward += my_drones[i].reward

            if new_reward != 0:
                rescued_number += new_reward

            # if display:
            #     time.sleep(0.002)

            if rescued_number == self.number_wounded_persons and rescued_all_time_step == 0:
                rescued_all_time_step = engine.elapsed_time

            end_real_time = time.time()
            real_time_elapsed = (end_real_time - start_real_time)
            if real_time_elapsed > self.real_time_limit:
                self.real_time_limit_reached = True
                terminate = True

            if terminate:
                engine.game_on = False

            # fps_display.update()

        last_image = engine.generate_playground_image()

        engine.terminate()

        score_exploration = my_map.explored_map.score()
        # my_map.explored_map.display()

        last_image_explo_lines = my_map.explored_map.get_pretty_map_explo_lines()
        last_image_explo_zones = my_map.explored_map.get_pretty_map_explo_zones()
        self.save_data.save_images(last_image, last_image_explo_lines, last_image_explo_zones, environment_type,
                                   num_round)

        return engine.elapsed_time, rescued_all_time_step, score_exploration, rescued_number, real_time_elapsed

    def go(self):
        for environment_type in MyMap.environment_series:
            print("*** Environment '{}'".format(environment_type.name.lower()))
            for i_try in range(0, self.nb_rounds):
                result = self.one_round(environment_type, i_try)
                (elapsed_time_step, rescued_all_time_step, score_exploration, rescued_number, real_time_elapsed) = result

                result_score = self.score_manager.compute_score(rescued_number,
                                                                score_exploration,
                                                                rescued_all_time_step)
                (final_score, percent_rescued, score_time_step) = result_score

                print("\t* Round n°{}".format(i_try),
                      ", real time elapsed = {:.1f}/{}s".format(real_time_elapsed, self.real_time_limit),
                      ", rescued number ={}/{}".format(rescued_number, self.number_wounded_persons),
                      ", exploration score =", "{:.1f}%".format(score_exploration * 100),
                      ", elapse time = {}/{} steps".format(elapsed_time_step, self.time_step_limit),
                      ", time to rescue all = {} steps".format(rescued_all_time_step),
                      ", final score =", "{:.2f}/100".format(final_score)
                      )
                if self.real_time_limit_reached:
                    print("\t\tThe real time limit of {}s is reached first.".format(self.real_time_limit))

                self.save_data.save_one_round(environment_type, i_try, percent_rescued, score_exploration,
                                              elapsed_time_step, rescued_all_time_step, score_time_step, final_score)
        self.save_data.fill_pdf()


if __name__ == "__main__":
    launcher = Launcher()
    launcher.go()
