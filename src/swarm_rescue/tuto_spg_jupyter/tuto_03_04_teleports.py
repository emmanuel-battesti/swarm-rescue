from simple_playgrounds.engine import Engine
from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.agent.agents import BaseAgent
from simple_playgrounds.playground.playgrounds import Teleports

my_playground = Teleports()

my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground.add_agent(my_agent)
engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
