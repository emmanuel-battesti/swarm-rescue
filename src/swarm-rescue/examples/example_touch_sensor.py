import random
import time

from simple_playgrounds.engine import Engine
from simple_playgrounds.playgrounds.layouts import LineRooms
from simple_playgrounds.agents.parts.controllers import External, Keyboard

from spg_overlay.drone import DroneAbstract


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message(self):
        pass

    def control(self):
        pass


def my_control(agent, the_touch_sensor):
    max_value = max(the_touch_sensor.sensor_values)
    # indices will contain indices with max values of the sensor
    indices = [i for i, x in enumerate(the_touch_sensor.sensor_values) if x == max(the_touch_sensor.sensor_values)]

    in_front = False
    for ind in indices:
        if 9 <= ind < 27:
            in_front = True
            break

    touched = False
    if max_value > 0.5 and in_front:
        touched = True
        # print(indices)
    # else:
    # print("---")

    command1 = {agent.grasp: 1, agent.longitudinal_force: 1.0, agent.rotation_velocity: random.uniform(-0.1, 0.1)}
    command2 = {agent.grasp: 1, agent.longitudinal_force: 0.0, agent.rotation_velocity: 1}
    if touched:
        command = command2
    else:
        command = command1

    return command


size_area = (700, 700)
my_playground = LineRooms(size=size_area, number_rooms=2, random_doorstep_position=True, doorstep_size=200)

my_drone = MyDrone(controller=External())
touch_sensor = my_drone.touch()

my_playground.add_agent(my_drone, ((80, 100), 0))

engine = Engine(playground=my_playground, time_limit=10000, screen=True)
engine.update_observations()

total_rew = 0
while engine.game_on:

    engine.update_screen()
    engine.update_observations()

    actions = {}
    for oneAgent in engine.agents:
        actions[oneAgent] = my_control(oneAgent, touch_sensor)
        total_rew += oneAgent.reward
        if oneAgent.reward != 0:
            print("total reward:", total_rew)

    terminate = engine.step(actions)

    time.sleep(0.002)

    if terminate:
        engine.terminate()

engine.terminate()
