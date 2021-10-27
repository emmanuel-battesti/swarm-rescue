import time

import pygame

from simple_playgrounds.engine import Engine

from maps.map_eating_candy import MyMapEatingCandy
from maps.map_fish import MyMapFish
from maps.map_random import MyMapRandom
from maps.map_rescue_wounded_persons import MyMapRescueWoundedPersons
from maps.map_compet_01 import MyMapCompet01

from solutions.my_drone_eating_candy import MyDroneEatingCandy
from solutions.my_drone_fish import MyDroneFish
from solutions.my_drone_random import MyDroneRandom
from solutions.my_drone_rescue_wounded_persons import MyDroneRescueWoundedPersons


class MyMap(MyMapRescueWoundedPersons):
    pass


class MyDrone(MyDroneRescueWoundedPersons):
    pass


class Launcher:
    def __init__(self):
        self.nb_rounds = 1
        self.total_reward = 0
        self.total_time = 0
        self.mean_time = 0
        self.my_map = MyMap()
        self.with_com = True

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
        my_drones = self.my_map.drones
        my_playground = self.my_map.playground

        engine = Engine(playground=my_playground, time_limit=self.my_map.time_limit, screen=True)
        clock = pygame.time.Clock()
        counter = 0

        while engine.game_on:

            # print("time=", engine.elapsed_time)
            engine.update_screen()
            engine.update_observations(grasped_invisible=True)

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
                self.total_reward += new_reward
                # print("elapsed_time=", engine.elapsed_time, ", total reward=", total_reward)

            time.sleep(0.002)

            if terminate or self.total_reward >= self.my_map.max_reward:
                engine.game_on = False

            # counter += 1
            # if counter % 20 == 0:
            #     print("FPS:", clock.get_fps())
            # clock.tick(60)

        engine.terminate()

        return engine.elapsed_time

    def go(self):
        total_time = 0
        for i in range(0, self.nb_rounds):
            elapsed_time = self.one_round()
            self.total_time += elapsed_time
            self.mean_time = self.total_time / (i + 1)
            print("*** Round", i, ", REWARDS =", self.total_reward, ", TOTAL TIME =", elapsed_time, ", MEAN TIME =",
                  self.mean_time)


if __name__ == "__main__":
    launcher = Launcher()
    launcher.go()
