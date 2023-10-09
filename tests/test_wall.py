import pytest

from resources import path_resources
from spg_overlay.entities.normal_wall import SrColorWall, NormalWall


class TestSrColorWall:

    #  Tests that a colored wall can be created with valid parameters
    def test_create_colored_wall_with_valid_parameters(self):
        # Create a colored wall with valid parameters
        wall = SrColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, color=(255, 0, 0))
    
        # Assert that the wall is an instance of SrColorWall
        assert isinstance(wall, SrColorWall)
    
        # Assert that the wall has the correct position and angle
        assert wall.wall_coordinates == ((5.0, 0.0), 1.5707963267948966)
    
        # Assert that the wall has the correct texture
        assert wall.texture.name == "Barrier_2_12.0_(255, 0, 0)"
