import time

import cv2
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
        self.total_time = 0
        self.mean_time = 0

        self.team_info = TeamInfo()

        self.my_map = MyMap()
        self.with_com = True

        self.score_manager = ScoreManager(number_drones=self.my_map.number_drones,
                                          time_step_limit=self.my_map.time_step_limit,
                                          real_time_limit=self.my_map.real_time_limit,
                                          total_number_wounded_persons=self.my_map.number_wounded_persons)

        # BUILD DRONES
        misc_data = MiscData(size_area=self.my_map.size_area,
                             number_drones=self.my_map.number_drones)
        drones = [MyDrone(identifier=i, misc_data=misc_data)
                  for i in
                  range(self.my_map.number_drones)]

        self.my_map.set_drones(drones)

        self.wounded = self.my_map.number_wounded_persons
        self.save_data = SaveData(self.team_info)

    def reset(self, environment_type):
        self.mean_time = 0

        self.my_map = MyMap(environment_type)
        self.with_com = True

        self.score_manager = ScoreManager(number_drones=self.my_map.number_drones,
                                          time_step_limit=self.my_map.time_step_limit,
                                          real_time_limit=self.my_map.real_time_limit,
                                          total_number_wounded_persons=self.my_map.number_wounded_persons,
                                          )

        # BUILD DRONES
        misc_data = MiscData(size_area=self.my_map.size_area,
                             number_drones=self.my_map.number_drones)
        drones = [MyDrone(identifier=i, misc_data=misc_data)
                  for i in
                  range(self.my_map.number_drones)]

        self.my_map.set_drones(drones)

    def define_all_messages(self):
        messages = []
        number_drones = len(self.my_map.drones)
        for i in range(0, number_drones):
            if self.with_com:
                msg_data = self.my_map.drones[i].define_message()
                one_message = (self.my_map.drones[i].communication, msg_data, None)
                messages.append(one_message)
        return messages

    def one_round(self, environment_type, num_round):
        self.reset(environment_type)
        my_drones = self.my_map.drones
        my_playground = self.my_map.playground

        engine = Engine(playground=my_playground, time_limit=self.my_map.time_step_limit, screen=self.display)

        fps_display = FpsDisplay(period_display=0.5)

        rescued_number = 0
        time_rescued_all = 0
        self.my_map.explored_map.reset()

        start_real_time = time.time()

        while engine.game_on:
            # print("time=", engine.elapsed_time)
            if self.display:
                engine.update_screen()

            engine.update_observations(grasped_invisible=True)

            self.my_map.explored_map.update(my_drones)

            # COMPUTE ALL THE MESSAGES
            messages = self.define_all_messages()

            # COMPUTE ACTIONS
            actions = {}
            for i in range(0, self.my_map.number_drones):
                actions[my_drones[i]] = my_drones[i].control()

            my_drones[0].display()

            terminate = engine.step(actions, messages)

            # REWARDS
            new_reward = 0
            for i in range(0, self.my_map.number_drones):
                new_reward += my_drones[i].reward

            if new_reward != 0:
                rescued_number += new_reward

            # if display:
            #     time.sleep(0.002)

            if rescued_number == self.my_map.number_wounded_persons and time_rescued_all == 0:
                time_rescued_all = engine.elapsed_time

            end_real_time = time.time()
            real_time_elapsed = (end_real_time - start_real_time)
            if real_time_elapsed > self.my_map.real_time_limit:
                print("The real time limit of {}s is reached !...".format(self.my_map.real_time_limit))
                terminate = True

            if terminate:
                engine.game_on = False

            # fps_display.update()

        last_image = engine.generate_playground_image()

        engine.terminate()

        score_exploration = self.my_map.explored_map.score()
        # self.my_map.explored_map.display()

        last_image_explo_lines = self.my_map.explored_map.get_pretty_map_explo_lines()
        last_image_explo_zones = self.my_map.explored_map.get_pretty_map_explo_zones()
        self.save_data.save_images(last_image, last_image_explo_lines, last_image_explo_zones, environment_type,
                                   num_round)

        return engine.elapsed_time, time_rescued_all, score_exploration, rescued_number

    def go(self):
        for environment_type in MyMap.environment_series:
            print("*** Environment '{}'".format(environment_type.name.lower()))
            for i_try in range(0, self.nb_rounds):
                elapsed_time_step, time_rescued_all, score_exploration, rescued_number = self.one_round(
                    environment_type,
                    i_try)

                self.total_time += elapsed_time_step
                self.mean_time = self.total_time / (i_try + 1)
                final_score, percent_rescued, score_time_step = self.score_manager.compute_score(rescued_number,
                                                                                                 score_exploration,
                                                                                                 time_rescued_all)
                print("\t* Round n°{}".format(i_try),
                      ", rescued number ={}/{}".format(rescued_number, self.my_map.number_wounded_persons),
                      ", exploration score =", "{:.1f}%".format(score_exploration * 100),
                      ", elapse time step = {}s".format(elapsed_time_step),
                      ", time to rescue all = {}s".format(time_rescued_all),
                      ", final score =", "{:.2f}/100".format(final_score)
                      )
                self.save_data.save_one_round(environment_type, i_try, percent_rescued, score_exploration,
                                              elapsed_time_step, time_rescued_all, score_time_step, final_score)
        self.save_data.fill_pdf()


if __name__ == "__main__":
    launcher = Launcher()
    launcher.go()
