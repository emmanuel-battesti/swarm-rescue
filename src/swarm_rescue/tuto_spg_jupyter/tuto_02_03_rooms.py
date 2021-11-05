from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.playground import GridRooms
from simple_playgrounds.engine import Engine

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


# We can build playgrounds with any number of rooms.
# We can also set the type of doorsteps, their size, and select from a list of wall themes.
my_playground = GridRooms(size=(400, 400),
                          room_layout=(3, 3),
                          random_doorstep_position=False,
                          doorstep_size=60)
engine = Engine(time_limit=10000,
                playground=my_playground,
                screen=True)

# Let say that we want an object to always appear in the middle-left room.
room = my_playground.grid_rooms[0][1]
position_center, shape = room.center, room.size

area = CoordinateSampler(center=position_center, area_shape='rectangle', size=shape)
circular_object = Physical(physical_shape='circle', radius=5, texture=[120, 230, 0])
my_playground.add_element(circular_object, area)

# plt_image(engine.generate_playground_image(plt_mode=True))

engine.run(update_screen=True)
engine.terminate()
