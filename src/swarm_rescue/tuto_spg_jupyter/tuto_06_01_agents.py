import time

from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import HeadAgent
from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.device.sensors import RgbCamera


# to display the sensors
import cv2

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = SingleRoom(size=(200, 200))

my_agent = HeadAgent(controller=Keyboard(), interactive=True)
my_agent.add_sensor(RgbCamera(my_agent.head, invisible_elements=my_agent.parts, fov=60, range=150))

my_playground.add_agent(my_agent)

pentagon_object = Physical(config_key='pentagon', graspable=True, mass=10)
my_playground.add_element(pentagon_object, ((170, 30), 0.5))

circular_object = Physical(physical_shape='circle', radius=10, texture=[120, 0, 230])
my_playground.add_element(circular_object, ((170, 160), -0.5))

engine = Engine(time_limit=10000, playground=my_playground, screen=True)

# plt_image(engine.generate_playground_image(plt_mode=True))
# plt.figure(figsize=(10, 10))
# plt_image(engine.generate_agent_image(my_agent, plt_mode=True))

while engine.game_on:

    engine.update_screen()

    actions = {}
    for agent in engine.agents:
        actions[agent] = agent.controller.generate_actions()

    terminate = engine.step(actions)
    engine.update_observations()

    # cv2.imshow('control panel', engine.generate_agent_image(my_agent))
    # cv2.waitKey(20)
    time.sleep(0.02)

    if terminate:
        engine.terminate()

engine.terminate()
cv2.destroyAllWindows()
