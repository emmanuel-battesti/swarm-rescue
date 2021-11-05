from simple_playgrounds.engine import Engine
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent
from simple_playgrounds.playground.playgrounds import Contacts
from simple_playgrounds.common.position_utils import CoordinateSampler

area_start = CoordinateSampler((150, 150), 'rectangle', size=(100, 100))
my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground = Contacts()
my_playground.add_agent(my_agent, area_start)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
