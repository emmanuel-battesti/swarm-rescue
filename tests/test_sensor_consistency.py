"""Ensure lidar values agree between shader and CPU ray computations."""
import random
from typing import Tuple
from itertools import product

import numpy as np
import pytest

from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.utils.misc_data import MiscData


def _collect_lidar_values(use_shaders: bool, position: Tuple[int, int],
                          seed: int) -> np.ndarray:
    """Spawn a motionless drone in a tiny playground and return one lidar sweep.

    All three sources of randomness have to be pinned, otherwise the two
    playgrounds built below are not the same scene: each one draws its own
    interactives, and the lidar then legitimately measures different distances.
    Measured on an identical scene, shader and CPU differ by ~0.37 px on average
    (max 1.42 px); comparing two unrelated scenes gave ~2.9 px, which says
    nothing about the shaders.
    """
    random.seed(seed)      # the `random` module
    np.random.seed(seed)   # the numpy global RNG
    # Pass use_shaders directly to constructor for proper initialization
    playground = ClosedPlayground(size=(600, 400), use_shaders=use_shaders, seed=seed)
    misc_data = MiscData(
        size_area=(600, 400), number_drones=1, max_timestep_limit=1000,
        max_walltime_limit=100
    )
    drone = DroneMotionless(identifier=0, misc_data=misc_data, noise=False)
    playground.add(drone, (position, 0))

    # Step a few times to ensure the sensors have initialized
    for _ in range(5):
        playground.step()

    lidar_values = drone.lidar_values()
    assert lidar_values is not None
    return np.array(lidar_values)


# helper seeds
SEEDS = [0, 42]
POSITIONS = [(-100, 0), (0, 0), (100, -50)]


# `list(...)` around the product: pytest requires a concrete sequence, a raw
# `product` iterator is deprecated (PytestRemovedIn10Warning) and will be an
# error in pytest 10.
@pytest.mark.parametrize("seed,pos", list(product(SEEDS, POSITIONS)))
def test_lidar_shader_vs_cpu_similarity(seed, pos):
    """Lidar values should be similar whether rays are computed on GPU or CPU.

    The tolerance is the measured shader/CPU discrepancy on an identical scene
    (mean 0.37 px, max 1.42 px), not an arbitrary number.

    `rtol` must stay at 0 here: the lidar range is 300 px, so an `rtol` of 0.3
    would tolerate a 90 px error and silently accept a badly broken shader.
    `atol=2.0` covers the last-pixel rounding that comes from sampling the ray
    at slightly different steps on GPU and CPU, and still catches a wrong hit
    distance (verified: an 8 px offset in the shader makes this test fail).
    """
    shader_values = _collect_lidar_values(use_shaders=True, position=pos, seed=seed)
    cpu_values = _collect_lidar_values(use_shaders=False, position=pos, seed=seed)

    np.testing.assert_allclose(
        shader_values,
        cpu_values,
        rtol=0.0,
        atol=2.0,
        err_msg="Lidar outputs diverge too much between shader and CPU ray tracing",
    )
