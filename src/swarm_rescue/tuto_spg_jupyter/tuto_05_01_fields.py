from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.contact import Candy
from simple_playgrounds.common.spawner import Spawner
from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent

my_playground = SingleRoom(size=(200, 200))
engine = Engine(time_limit=10000, playground=my_playground, screen=True)

area = CoordinateSampler(center=(100, 100), area_shape='circle', radius=60)
spawner = Spawner(probability=0.05, production_limit=20, max_elements_in_playground=10, element_produced=Candy, production_area=area)
my_playground.add_spawner(spawner)

my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground.add_agent(my_agent)

engine.run(update_screen=True, print_rewards=True)
engine.terminate()
