"""
Integration test for DisappearingWall and DisappearingBox with playground reset.
This test ensures that disappearing walls and boxes work correctly with the full
playground reset mechanism.
"""
import sys
import pathlib

# Insert the parent directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.disappearing_wall import DisappearingWall, DisappearingBox
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


def test_disappearing_elements_with_playground_reset():
    """Test that disappearing elements work correctly with playground reset."""

    # Create a simple playground without drones
    playground = ClosedPlayground(size=(400, 400))

    # Add a disappearing wall that disappears after 5 timesteps
    wall = DisappearingWall(
        pos_start=(100, 100),
        pos_end=(100, 200),
        disappear_after_timesteps=5
    )
    playground.add(wall, wall.wall_coordinates)

    # Add a disappearing box that disappears after 8 timesteps
    box = DisappearingBox(
        up_left_point=(200, 200),
        width=50,
        height=50,
        disappear_after_timesteps=8
    )
    playground.add(box, box.wall_coordinates)

    # Initial state
    assert wall.disappeared is False
    assert box.disappeared is False
    assert wall._creation_timestep is None
    assert box._creation_timestep is None

    # Run 10 timesteps - both should disappear
    for _ in range(10):
        playground.step()

    # After 10 timesteps, both should have disappeared
    assert wall.disappeared is True
    assert box.disappeared is True
    assert wall._creation_timestep == 0
    assert box._creation_timestep == 0

    # Reset the playground
    playground.reset()

    # After reset, both should be back and timers reset
    assert wall.disappeared is False
    assert box.disappeared is False
    assert wall._creation_timestep is None
    assert box._creation_timestep is None

    # Run another 3 timesteps - neither should disappear yet
    for _ in range(3):
        playground.step()

    assert wall.disappeared is False
    assert box.disappeared is False

    # Run 3 more timesteps (total 6) - wall should disappear, box should not
    for _ in range(3):
        playground.step()

    assert wall.disappeared is True
    assert box.disappeared is False

    # Run 3 more timesteps (total 9) - box should now disappear too
    for _ in range(3):
        playground.step()

    assert wall.disappeared is True
    assert box.disappeared is True

    print("Integration test passed!")


if __name__ == "__main__":
    test_disappearing_elements_with_playground_reset()

