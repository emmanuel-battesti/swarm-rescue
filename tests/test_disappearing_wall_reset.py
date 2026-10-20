"""
Test to verify that DisappearingWall and DisappearingBox reset properly.
This test ensures that the disappearance timer is reset when the playground resets.
"""

class MockPlayground:
    """Mock playground for testing."""
    def __init__(self):
        self.timestep = 0
        self.removed_elements = []

    def remove(self, element):
        """Mock remove method."""
        self.removed_elements.append(element)


def test_disappearing_wall_reset():
    """Test that DisappearingWall resets properly."""
    from swarm_rescue.simulation.elements.disappearing_wall import DisappearingWall

    # Create a wall that disappears after 10 timesteps
    wall = DisappearingWall(
        pos_start=(0, 0),
        pos_end=(100, 0),
        disappear_after_timesteps=10
    )

    # Set up mock playground
    mock_pg = MockPlayground()
    wall._playground = mock_pg

    # Simulate timesteps until disappearance
    for i in range(15):
        mock_pg.timestep = i
        wall.pre_step()

    # Verify the wall has disappeared
    assert wall.disappeared is True
    assert wall._creation_timestep == 0
    assert len(mock_pg.removed_elements) == 1

    # Reset the wall
    wall.reset()

    # Verify reset worked correctly
    assert wall.disappeared is False
    assert wall._creation_timestep is None

    # Clear removed elements list
    mock_pg.removed_elements.clear()
    mock_pg.timestep = 0

    # Simulate timesteps again - wall should disappear again after 10 timesteps
    for i in range(15):
        mock_pg.timestep = i
        wall.pre_step()

    # Verify the wall disappeared again
    assert wall.disappeared is True
    assert wall._creation_timestep == 0
    assert len(mock_pg.removed_elements) == 1


def test_disappearing_box_reset():
    """Test that DisappearingBox resets properly."""
    from swarm_rescue.simulation.elements.disappearing_wall import DisappearingBox

    # Create a box that disappears after 10 timesteps
    box = DisappearingBox(
        up_left_point=(0, 0),
        width=50,
        height=50,
        disappear_after_timesteps=10
    )

    # Set up mock playground
    mock_pg = MockPlayground()
    box._playground = mock_pg

    # Simulate timesteps until disappearance
    for i in range(15):
        mock_pg.timestep = i
        box.pre_step()

    # Verify the box has disappeared
    assert box.disappeared is True
    assert box._creation_timestep == 0
    assert len(mock_pg.removed_elements) == 1

    # Reset the box
    box.reset()

    # Verify reset worked correctly
    assert box.disappeared is False
    assert box._creation_timestep is None

    # Clear removed elements list
    mock_pg.removed_elements.clear()
    mock_pg.timestep = 0

    # Simulate timesteps again - box should disappear again after 10 timesteps
    for i in range(15):
        mock_pg.timestep = i
        box.pre_step()

    # Verify the box disappeared again
    assert box.disappeared is True
    assert box._creation_timestep == 0
    assert len(mock_pg.removed_elements) == 1


if __name__ == "__main__":
    test_disappearing_wall_reset()
    test_disappearing_box_reset()
    print("All tests passed!")

