from simple_playgrounds.playgrounds.collection.test.test_playgrounds import Teleports
from simple_playgrounds.engine import Engine
from simple_playgrounds.agents.parts.controllers import Keyboard
from simple_playgrounds.agents.agents import BaseAgent

my_playground = Teleports()

my_agent = BaseAgent(controller=Keyboard(), interactive=True)
my_playground.add_agent(my_agent)
engine = Engine(my_playground, 10000, screen=True)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
