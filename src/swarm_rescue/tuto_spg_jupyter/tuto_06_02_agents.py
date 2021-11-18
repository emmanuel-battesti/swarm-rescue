from simple_playgrounds.engine import Engine
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent
from simple_playgrounds.device.sensors import RgbCamera, Lidar, SemanticCones, SemanticRay, Touch, TopdownLocal

# to display the sensors
import cv2

# matplotlib inline
import matplotlib.pyplot as plt
# from simple_playgrounds.playground.playgrounds import Basics
from simple_playgrounds.playground.playgrounds import Basics


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = Basics()

my_agent = BaseAgent(controller=Keyboard(), interactive=True)

my_agent.add_sensor(RgbCamera(my_agent.base_platform, invisible_elements=my_agent.parts))
my_agent.add_sensor(Lidar(my_agent.base_platform, invisible_elements=my_agent.parts))
my_agent.add_sensor(SemanticCones(my_agent.base_platform, invisible_elements=my_agent.parts, only_front=True))
my_agent.add_sensor(SemanticRay(my_agent.base_platform, invisible_elements=my_agent.parts, only_front=True))
# my_agent.add_sensor(PerfectLidar(my_agent.base_platform, invisible_elements=my_agent.parts, only_front=True))
my_agent.add_sensor(Touch(my_agent.base_platform, invisible_elements=my_agent.parts))
my_agent.add_sensor(TopdownLocal(my_agent.base_platform, invisible_elements=my_agent.parts))

my_playground.add_agent(my_agent)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)

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
# noinspection PyUnresolvedReferences
cv2.destroyAllWindows()
