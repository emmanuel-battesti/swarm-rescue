import sys
import pathlib

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.normal_wall import ColorWall





class TestColorWall:

    #  Tests that a colored wall can be created with valid parameters
    def test_create_colored_wall_with_valid_parameters(self):
        # Create a colored wall with valid parameters
        wall1 = ColorWall(pos_start=(0, 0), pos_end=(10, 0),
                         wall_thickness=2, color=(255, 0, 0))

        # Assert that the wall is an instance of ColorWall
        assert isinstance(wall1, ColorWall)

        # Assert that the wall has the correct position and angle
        assert wall1.wall_coordinates == ((5.0, 0.0), 0.0)

        # Assert that the wall has the correct texture
        assert wall1.texture.name == "Wall_5_0_0_12.0"

        # Create a colored wall with valid parameters
        wall2 = ColorWall(pos_start=(0, 0), pos_end=(0, 10),
                         wall_thickness=2, color=(255, 0, 0))

        # Assert that the wall is an instance of ColorWall
        assert isinstance(wall2, ColorWall)

        # Assert that the wall has the correct position and angle
        assert wall2.wall_coordinates == ((0.0, 5.0), 1.5707963267948966)

        # Assert that the wall has the correct texture
        assert wall2.texture.name == "Wall_0_5_90_12.0"
