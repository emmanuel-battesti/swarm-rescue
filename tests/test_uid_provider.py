"""
Tests for the `UidProvider` seam between the sensors and the rendering.

The point of the interface is that the sensors can be exercised against
anything that produces a uid image -- including a fake one, with no GPU and no
window. These tests do exactly that: they run the CPU ray path on a
hand-written image, which was impossible while `RayCompute` built and drew its
own `TopDownView`.
"""

import pathlib
import sys

import numpy as np

# Insert the 'src' and 'examples' directories into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.ray_sensors.ray_compute import RayCompute
from swarm_rescue.simulation.ray_sensors.uid_provider import UidProvider


class FakeUidProvider:
    """
    A uid image built in numpy, with no window and no OpenGL.

    Only the handful of methods the sensors actually call are needed; that is
    the whole value of the interface.
    """

    def __init__(self, image: np.ndarray, center=(0.0, 0.0), zoom: float = 1.0):
        self._image = image
        self._center = center
        self._zoom = zoom
        self.render_count = 0

    @property
    def center(self):
        return self._center

    @property
    def width(self) -> int:
        return self._image.shape[1]

    @property
    def height(self) -> int:
        return self._image.shape[0]

    @property
    def zoom(self) -> float:
        return self._zoom

    def render_uids(self) -> None:
        self.render_count += 1

    def read_uid_image(self) -> np.ndarray:
        return self._image

    def bind_uid_texture(self) -> None:
        pass


class FakeSensor:
    """Just enough of a `RaySensor` for the CPU path to run."""

    def __init__(self, position=(100.0, 100.0), angle=0.0,
                 resolution=3, n_points=301, max_range=300.0):
        self.position = position
        self.angle = angle
        self.resolution = resolution
        self.n_points = n_points
        self.max_range = max_range
        self.fov = 2 * np.pi
        self.anchor = type("Anchor", (), {"uid": 42})()
        self.invisible_ids = []
        self.require_invisible_update = False
        self.hitpoints = None
        # Rays pointing straight right, i.e. along +x in world units.
        self.end_positions = np.array(
            [[max_range, 0.0] for _ in range(resolution)], dtype=float
        ).T

    def update_hitpoints(self, hitpoints):
        self.hitpoints = hitpoints


def _provider_with_wall():
    """A 200x200 uid image with a vertical wall at pixel x=150."""
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    image[:, 150:, :] = (7, 0, 0)  # uid 7, written as (blue, green, red)
    return FakeUidProvider(image)


def test_the_fake_satisfies_the_protocol():
    """The interface must be structural, so a duck-typed object is enough."""
    assert isinstance(_provider_with_wall(), UidProvider)


def test_ray_compute_runs_against_a_fake_provider():
    """The CPU path must work with a plain numpy image."""
    provider = _provider_with_wall()
    compute = RayCompute(ctx=None, uid_provider=provider, use_shader=False)
    sensor = FakeSensor(position=(0.0, 0.0))
    compute.add(sensor)

    compute.update_sensors()

    assert provider.render_count == 1, "the image must be drawn before being read"
    assert sensor.hitpoints is not None
    # (resolution, 10): 2 view pos + 2 abs pos + 2 rel pos + 2 center + id + dist
    assert sensor.hitpoints.shape == (3, 10)


def test_the_fake_provider_is_not_replaced_by_a_real_view():
    """
    `RayCompute` must keep the provider it was given.

    A regression here would mean the sensor had gone back to building its own
    view, i.e. that the model depends on the presentation again.
    """
    provider = _provider_with_wall()
    compute = RayCompute(ctx=None, uid_provider=provider, use_shader=False)

    assert compute.uid_provider is provider


def test_the_wall_is_detected_at_the_expected_distance():
    """
    Sanity check on the fixture itself.

    A uid image full of walls is useless as a test fixture if the numbers that
    come out are wrong.

    The drone sits at world (0, 0), which with the provider defaults (center
    (0,0), zoom 1, 200x200 image) is the middle of the image, pixel (100, 100).
    The wall starts at pixel x=150, so every ray must stop 50 px away -- not at
    max_range, which is what a miss would report.
    """
    provider = _provider_with_wall()
    compute = RayCompute(ctx=None, uid_provider=provider, use_shader=False)
    sensor = FakeSensor(position=(0.0, 0.0))
    compute.add(sensor)

    compute.update_sensors()

    distances = sensor.hitpoints[:, 9]
    assert np.allclose(distances, 50.0), (
        f"expected every ray to stop 50 px from the drone, got {distances}"
    )

    # The hit must also carry the uid 7, recombined from the three channels.
    assert np.all(sensor.hitpoints[:, 8] == 7)


def test_a_blank_image_reports_the_max_range():
    """Nothing in sight must read as max_range, not as a hit at distance 0."""
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    provider = FakeUidProvider(image)
    compute = RayCompute(ctx=None, uid_provider=provider, use_shader=False)
    sensor = FakeSensor(position=(100.0, 100.0))
    compute.add(sensor)

    compute.update_sensors()

    assert np.allclose(sensor.hitpoints[:, 9], 300.0)
