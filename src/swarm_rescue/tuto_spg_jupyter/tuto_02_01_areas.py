from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.basic import Physical
from simple_playgrounds.common.position_utils import CoordinateSampler

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = SingleRoom(size=(300, 300))

# we use the option screen=True to use a keyboard controlled agent later on.
engine = Engine(time_limit=10000, playground=my_playground, screen=False)

# The initial position of a scene element has to be specified.
# Instead of a position, you can define an area where the position will be sampled uniformly.
#
# In the following, we create a circular area sampler centered at (50, 50) and of radius 60.
# We generate 10 objects. Note that we add them without overlapping, meaning that if the playground
# can't find a suitable position, it will raise an error.
area = CoordinateSampler((50, 50), area_shape='circle', radius=60)
for i in range(10):
    circular_object = Physical(physical_shape='circle', radius=5, texture=[120, 230, 0])
    try:
        my_playground.add_element(circular_object, area, allow_overlapping=False)
    except:
        print('Failed to place object')

# Other possible shapes are rectangle, or gaussian. We will allow overlapping for the following added element.
# gaussian area
area = CoordinateSampler((250, 50), area_shape='gaussian', radius=80, std=100)
for i in range(20):
    circular_object = Physical(physical_shape='circle', radius=5, texture=[120, 0, 240])
    my_playground.add_element(circular_object, area)

area = CoordinateSampler((150, 150), area_shape='rectangle', size=(70, 40))
for i in range(20):
    circular_object = Physical(physical_shape='circle', radius=5, texture=[0, 120, 120])
    my_playground.add_element(circular_object, area)

# Playground provide their own areas
room = my_playground.grid_rooms[0][0]
center_area, size_area = room.center, (room.width, room.length)
print(center_area, size_area)
area_all = CoordinateSampler(center=center_area, area_shape='rectangle', size=size_area)
for i in range(50):
    circular_object = Physical(physical_shape='circle', radius=5, texture=[250, 100, 0])
    try:
        my_playground.add_element(circular_object, area_all, allow_overlapping=False)
    except:
        print('Failed to place object')

# playgrounds provide quarter areas of rooms.
center_partial_area, size_partial_area = room.get_partial_area('down-right')
print(center_partial_area, size_partial_area)
area_top = CoordinateSampler(center=center_partial_area, area_shape='rectangle', size=size_partial_area)
for i in range(50):
    circular_object = Physical(physical_shape='circle', radius=7, texture=[200, 100, 250])
    try:
        my_playground.add_element(circular_object, area_top, allow_overlapping=False)
    except:
        print('Failed to place object')

engine.reset()

plt_image(engine.generate_playground_image(plt_mode=True))

engine.terminate()
