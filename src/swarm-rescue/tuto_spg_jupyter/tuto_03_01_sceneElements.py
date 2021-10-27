from simple_playgrounds.playgrounds.layouts import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.elements.collection.gem import Coin
from simple_playgrounds.elements.collection.contact import VisibleEndGoal, Candy
from simple_playgrounds.elements.collection.activable import VendingMachine
from simple_playgrounds.agents.parts.controllers import Keyboard
from simple_playgrounds.agents.agents import BaseAgent

my_playground = SingleRoom(size=(200, 200))

end_goal = VisibleEndGoal()
my_playground.add_element(end_goal, ((70, 70), 0))

candy = Candy()
my_playground.add_element(candy, ((140, 140), 0))

vending_machine = VendingMachine(100)
my_playground.add_element(vending_machine, ((50, 40), 0))

coin = Coin(graspable=True, vending_machine=vending_machine)
my_playground.add_element(coin, ((30, 140), 0))

my_agent = BaseAgent(controller=Keyboard(), interactive=True, radius=10)
my_playground.add_agent(my_agent)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
