from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent

# matplotlib inline
import matplotlib.pyplot as plt


# function to draw an image with matplotlib
def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


# SingleRoom : Playground composed of a single room
my_playground = SingleRoom(size=(1500, 1000))

# A pygame screen is created by default if one agent is controlled by Keyboard. You can terminate an engine using the Q key.
# Screen is intended for debugging or playing by a human (using Keyboard).
# If time limit is defined in playground and engine, engine prevails. If time limit is False, environment never terminates.
# Params:
# playground – obj: 'Playground'): Playground where the agents will be placed.
# time_limit – obj: 'int'): Number of time steps that the playground will be run. Can also be defined in playground.
# screen – If True, a pygame screen is created for display. Default: False
# screen : false is ok, to draw only in matplotlib
# debug – If True, scene is displayed using debug colors instead of textures.
engine = Engine(time_limit=10000, playground=my_playground, screen=True)

circular_object = Physical(physical_shape='circle', radius=100, texture=[120, 230, 0])
# position x=200, y=400, theta=0
my_playground.add_element(circular_object, ((200, 400), 0))

# We can use already existing configurations for basic objects. Every parameter that we add as a keyword argument will
# overwrite the default parameter.
# As an example, we will make a new element which is movable. Note that movable objets require that you set a mass (duh).
other_circular_object = Physical(config_key='circle', radius=50, mass=10, movable=True)
my_playground.add_element(other_circular_object, ((1200, 700), 0))

my_agent = BaseAgent(controller=Keyboard(), radius=100)
my_playground.add_agent(my_agent)

# you can terminate the game by pressing q.
# this command is a blocking one
engine.run(update_screen=True)
engine.terminate()

# For displaying with matplotlib, use plt_mode = True
# topdown_img : image of the playground
topdown_img = engine.generate_playground_image(plt_mode=True)
# draw topdown_img
plt_image(topdown_img)
