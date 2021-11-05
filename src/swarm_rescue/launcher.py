import time
import pygame
from simple_playgrounds.engine import Engine
from spg_overlay.score_manager import ScoreManager

from maps.map_lidar_communication import MyMapLidarCommunication
from maps.map_random import MyMapRandom
from maps.map_compet_01 import MyMapCompet01

from solutions.my_drone_lidar_communication import MyDroneLidarCommunication
from solutions.my_drone_random import MyDroneRandom


class MyMap(MyMapLidarCommunication):
    pass


class MyDrone(MyDroneLidarCommunication):
    pass


class Launcher:
    def __init__(self):
        self.nb_rounds = 1
        self.rescued_number = 0
        self.score_exploration = 0
        self.total_time = 0
        self.mean_time = 0

        self.my_map = MyMap()
        self.with_com = True

        self.score_manager = ScoreManager(number_drones=self.my_map.number_drones,
                                          time_step_limit=self.my_map.time_step_limit,
                                          real_time_limit=self.my_map.real_time_limit,
                                          total_number_wounded_persons=self.my_map.number_wounded_persons)

        # BUILD DRONES
        drones = [MyDrone(identifier=i)
                  for i in
                  range(self.my_map.number_drones)]

        self.my_map.set_drones(drones)

    def reset(self):
        self.rescued_number = 0
        self.score_exploration = 0
        self.mean_time = 0

        self.my_map = MyMap()
        self.with_com = True

        self.score_manager = ScoreManager(number_drones=self.my_map.number_drones,
                                          time_step_limit=self.my_map.time_step_limit,
                                          real_time_limit=self.my_map.real_time_limit,
                                          total_number_wounded_persons=self.my_map.number_wounded_persons,
                                          )

        # BUILD DRONES
        drones = [MyDrone(identifier=i)
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

    def one_round(self):
        self.reset()
        my_drones = self.my_map.drones
        my_playground = self.my_map.playground

        engine = Engine(playground=my_playground, time_limit=self.my_map.time_step_limit, screen=True)

        clock = pygame.time.Clock()
        counter = 0

        self.rescued_number = 0
        time_rescued_all = 0
        self.my_map.explored_map.reset()

        start_real_time = time.time()

        while engine.game_on:

            # print("time=", engine.elapsed_time)
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
                self.rescued_number += new_reward

            time.sleep(0.002)

            if self.rescued_number == self.my_map.number_wounded_persons and time_rescued_all == 0:
                time_rescued_all = engine.elapsed_time

            end_real_time = time.time()
            real_time_elapsed = (end_real_time - start_real_time)
            if real_time_elapsed > self.my_map.real_time_limit:
                print("The real time limit is reached !...")
                terminate = True

            if terminate:
                engine.game_on = False

            # counter += 1
            # if counter % 20 == 0:
            #     print("FPS:", clock.get_fps())
            # clock.tick(60)

        engine.terminate()

        self.score_exploration = self.my_map.explored_map.score()
        # self.my_map.explored_map.display()

        return engine.elapsed_time, time_rescued_all, self.score_exploration, self.rescued_number

    def go(self):
        total_time = 0
        for i in range(0, self.nb_rounds):
            elapsed_time_step, time_rescued_all, score_exploration, rescued_number = self.one_round()
            self.total_time += elapsed_time_step
            self.mean_time = self.total_time / (i + 1)
            final_score = self.score_manager.compute_score(rescued_number, score_exploration, time_rescued_all)
            print("*** Round", i,
                  ", rescued number =", rescued_number,
                  ", exploration score =", "{:.2f}".format(score_exploration),
                  ", elapse time step =", elapsed_time_step,
                  ", time to rescue all =", time_rescued_all,
                  ", final score = ", "{:.2f}".format(final_score)
                  )


if __name__ == "__main__":
    launcher = Launcher()
    launcher.go()
