from simple_playgrounds.playground import LineRooms
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.activable import OpenCloseSwitch
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = LineRooms(size=(400, 200), number_rooms=2, random_doorstep_position=True, doorstep_size=60)
engine = Engine(time_limit=10000, playground=my_playground, screen=True)

# Generate a door for a doorstep
room_left = my_playground.grid_rooms[0][0]

doorstep = room_left.doorstep_right

door = doorstep.generate_door()
my_playground.add_element(door)

switch = OpenCloseSwitch(door=door)
position_switch = room_left.get_random_position_on_wall(wall_location='right', element=switch)
my_playground.add_element(switch, position_switch)

# We add an agent, that you can control with a keyboard. Go to the switch and activate it with A.
my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground.add_agent(my_agent, ((50, 50), 0))

# plt_image(engine.generate_playground_image(plt_mode=True))

engine.run(update_screen=True)
engine.terminate()
