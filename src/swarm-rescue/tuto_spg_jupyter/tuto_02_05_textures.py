from simple_playgrounds.common.texture import UniqueRandomTilesTexture
from simple_playgrounds.playgrounds.layouts import GridRooms
from simple_playgrounds.engine import Engine

# matplotlib inline
import matplotlib.pyplot as plt


def plt_image(img):
    plt.axis('off')
    plt.imshow(img)
    plt.show()


custom_texture = UniqueRandomTilesTexture(color_min=(0, 100, 0),
                                          color_max=(250, 100, 0),
                                          n_colors=10,
                                          size=(200, 200))

my_playground = GridRooms(size=(600, 600),
                          room_layout=(3, 3),
                          random_doorstep_position=False,
                          doorstep_size=80,
                          wall_params=custom_texture)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)
engine.run(update_screen=True)
engine.terminate()
