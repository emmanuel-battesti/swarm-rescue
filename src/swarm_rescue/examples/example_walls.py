"""
This program can be launched directly.
Example of how to draw wall in the playground
"""

from simple_playgrounds.element.elements.basic import Wall
from simple_playgrounds.engine import Engine
from simple_playgrounds.playground import SingleRoom

size_area = (700, 700)
my_playground = SingleRoom(size=size_area)

wall1 = Wall(start_point=(100, 100), end_point=(600, 200), wall_depth=20, texture=[123, 234, 0])
my_playground.add_element(wall1)
wall2 = Wall(start_point=(500, 100), end_point=(200, 600), wall_depth=10, texture=[250, 234, 0])
my_playground.add_element(wall2)
wall3 = Wall(start_point=(560, 500), end_point=(200, 450), wall_depth=10, texture=[250, 0, 125])
my_playground.add_element(wall3)

engine = Engine(playground=my_playground, time_limit=10000, screen=True)
engine.run(update_screen=True)
engine.terminate()
