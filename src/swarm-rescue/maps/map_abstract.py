from abc import ABC, abstractmethod


class MapAbstract(ABC):
    @abstractmethod
    def set_drones(self):
        pass
