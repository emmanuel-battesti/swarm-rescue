from simple_playgrounds.playground import GridRooms
from simple_playgrounds.engine import Engine

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


my_playground = GridRooms(size=(600, 600),
                          room_layout=(4, 4),
                          random_doorstep_position=False,
                          doorstep_size=80,
                          wall_type='colorful')

engine = Engine(playground=my_playground, screen=True)

engine.run(update_screen=True)
engine.terminate()
