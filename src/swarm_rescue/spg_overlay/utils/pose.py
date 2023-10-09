import numpy as np


class Position:
    def __init__(self):
        self.data = np.zeros((2, ))

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __repr__(self):
        return 'Position({})'.format(self.data)

    def set(self, x, y):
        self.data[0] = x
        self.data[1] = y

    @property
    def x(self):
        return self.data[0]

    @property
    def y(self):
        return self.data[1]


# class Pose:
#     def __init__(self, position=Position(), orientation=0.0):
#         if not isinstance(position, Position):
#             print("type position=", type(position))
#             raise TypeError("position must be an instance of Position")
#         self.position: Position = position
#         self.orientation: float = orientation

class Pose:
    def __init__(self, position=np.zeros(2, ), orientation=0.0):
        if not isinstance(position, np.ndarray):
            print("type position=", type(position))
            raise TypeError("position must be an instance of np.ndarray")
        self.position: np.array = position
        self.orientation: float = orientation
