
from simple_playgrounds.engine import Engine
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent
from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.device.sensors import RgbCamera
from simple_playgrounds.playground.playgrounds import Basics

# to display the sensors
import cv2

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = Basics()
my_agent = BaseAgent(initial_position=(100, 50, 1.15), controller=Keyboard(), interactive=True)

circular_object = Physical(physical_shape='circle', radius=10, texture=[120, 230, 0], graspable=True, mass=5)
my_playground.add_element(circular_object, ((150, 30), 1.8))

camera = RgbCamera(circular_object, invisible_elements=circular_object)
my_agent.add_sensor(camera)

my_playground.add_agent(my_agent)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.update_observations()
# engine.run(update_screen=True, print_rewards=True)

# plt_image(engine.generate_playground_image(plt_mode=True))
# plt.figure(figsize=(15, 10))
# cv2.imshow('act', my_agent.generate_actions_image())
# plt_image(engine.generate_agent_image(my_agent, plt_mode=True))

while engine.game_on:

    engine.update_screen()

    actions = {}
    for agent in engine.agents:
        actions[agent] = agent.controller.generate_actions()

    terminate = engine.step(actions)
    engine.update_observations()

    cv2.imshow('control panel', engine.generate_agent_image(my_agent))
    cv2.waitKey(20)

    if terminate:
        engine.terminate()

engine.terminate()
cv2.destroyAllWindows()
