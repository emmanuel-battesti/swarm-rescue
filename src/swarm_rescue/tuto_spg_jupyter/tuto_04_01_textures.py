from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.common.texture import ColorTexture, RandomUniformTexture, RandomTilesTexture, \
    MultipleCenteredStripesTexture, CenteredRandomTilesTexture

my_playground = SingleRoom(size=(200, 200))

# The most basic texture is a uniform color.
elem = Physical(physical_shape='square', radius=10, texture=[123, 234, 0])
my_playground.add_element(elem, ((50, 50), 0))

elem = Physical(physical_shape='circle', radius=10, texture=ColorTexture(color=(222, 0, 0)))
my_playground.add_element(elem, ((100, 50), 0))

elem = Physical(physical_shape='pentagon', radius=10,
                texture={'texture_type': 'color', 'color': (0, 0, 222)})
my_playground.add_element(elem, ((150, 50), 0))

tex_uniform = RandomUniformTexture(color_min=(100, 100, 0), color_max=(200, 250, 0))
elem = Physical(physical_shape='pentagon', radius=10, texture=tex_uniform)
my_playground.add_element(elem, ((50, 100), 0))

tex_tiles = RandomTilesTexture(color_min=(150, 100, 0), color_max=(200, 250, 0), size_tiles=5)
elem = Physical(physical_shape='rectangle', size=(20, 30), texture=tex_tiles)
my_playground.add_element(elem, ((100, 100), 0))

tex_polar = MultipleCenteredStripesTexture(color_1=(200, 100, 50), color_2=(100, 100, 150), n_stripes=5)
elem = Physical(physical_shape='pentagon', radius=20, texture=tex_polar)
my_playground.add_element(elem, ((50, 150), 0))

tex_random_tiles_centered = CenteredRandomTilesTexture(color_min=(100, 0, 100), color_max=(200, 0, 200),
                                                       size_tiles=20)
elem = Physical(physical_shape='hexagon', radius=20, texture=tex_random_tiles_centered)
my_playground.add_element(elem, ((100, 150), 0))

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True, print_rewards=True)
engine.terminate()
