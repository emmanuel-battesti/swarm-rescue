from simple_playgrounds.playgrounds.collection.test.test_playgrounds import Gems
from simple_playgrounds.engine import Engine
from simple_playgrounds.agents.parts.controllers import Keyboard
from simple_playgrounds.agents.agents import BaseAgent

my_playground = Gems()

my_agent = BaseAgent(controller=Keyboard(), interactive=True, radius=10)
my_playground.add_agent(my_agent)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
