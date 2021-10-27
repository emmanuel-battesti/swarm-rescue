from simple_playgrounds.playgrounds.layouts import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.elements.collection.contact import Candy
from simple_playgrounds.elements.field import Field
from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.agents.parts.controllers import Keyboard
from simple_playgrounds.agents.agents import BaseAgent

my_playground = SingleRoom(size=(200, 200))
engine = Engine(time_limit=10000, playground=my_playground, screen=True)

area = CoordinateSampler(center=(100, 100), area_shape='circle', radius=60)
field = Field(probability=0.05, production_limit=20, max_elements_in_playground=10, element_produced=Candy, production_area=area)
my_playground.add_field(field)

my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground.add_agent(my_agent)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
