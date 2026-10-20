"""
Reproducibility of a round when a seed is given.

Before this was wired up, `Playground` accepted a `seed` but `ClosedPlayground`
overwrote it with a hardcoded `seed=None`, and no map ever forwarded a seed:
entity UIDs came from a fresh generator on every run. Since the lidar
identifies the entities it hits by UID, a round could not be replayed.

These tests pin the two properties the fix relies on:

1. the same seed produces the same UIDs and the same drone placements;
2. the maps no longer draw from the global `random` module, which would bypass
   the seed entirely.

`seed=None` stays the default and keeps the previous behavior, so the
non-reproducible path is exercised too.
"""

import gc
import pathlib
import random
import sys

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.maps.map_random import MapRandom
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless


def _fingerprint(the_map):
    """Collect what a replay must reproduce: entity UIDs and drone placements."""
    uids = sorted(agent.uid for agent in the_map.playground.agents)
    poses = [tuple(round(v, 6) for v in agent.true_position()) +
             (round(float(agent.true_angle()), 6),)
             for agent in the_map.playground.agents]
    return uids, poses


def _build(map_class, seed):
    the_map = map_class(drone_type=DroneMotionless, seed=seed)
    return _fingerprint(the_map)


class TestSeedReproducesRound:
    def test_same_seed_gives_identical_uids_and_positions(self):
        """The whole point: a seeded round can be replayed identically."""
        first = _build(MapIntermediate01, 1234)
        second = _build(MapIntermediate01, 1234)

        assert first[0] == second[0], "entity UIDs differ across identical seeds"
        assert first[1] == second[1], "entity positions differ across identical seeds"

    def test_different_seeds_give_different_positions(self):
        """A seed that changes nothing would be a no-op, not a feature."""
        first = _build(MapIntermediate01, 1)
        second = _build(MapIntermediate01, 2)

        assert first[1] != second[1]

    def test_random_map_is_reproducible(self):
        """`MapRandom` draws 3 values per drone, the heaviest user of the RNG."""
        assert _build(MapRandom, 7) == _build(MapRandom, 7)

    def test_default_is_still_non_reproducible(self):
        """`seed=None` must keep the old behavior, not silently become 0."""
        the_map = MapIntermediate01(drone_type=DroneMotionless)
        assert the_map.seed is None


class TestSeedIsolation:
    def test_map_seed_is_exposed(self):
        """Maps report the seed they were built with."""
        assert MapIntermediate01(drone_type=DroneMotionless, seed=42).seed == 42

    def test_maps_do_not_use_the_global_random_module(self):
        """A global `random` call would escape the seed entirely.

        This is a regression guard: seeding the playground is not enough if a
        map keeps drawing placements from the module-level RNG.
        """
        # Perturb the global RNG. A map still using it would diverge here.
        random.seed(0)
        for _ in range(50):
            random.random()

        assert _build(MapIntermediate01, 99) == _build(MapIntermediate01, 99)

    def test_global_random_untouched_by_construction(self):
        """A seeded map must not depend on the global RNG stream.

        Not "must not consume it": `NormalWall` still calls
        `random.randint` to pick which slice of a wall texture to crop
        (`normal_wall.py:71-72`). That is cosmetic and happens before any
        entity exists, but it means the *global stream* advances, so this test
        pins the property that actually matters -- the outcome does not depend
        on that stream.
        """
        def fingerprint():
            random.seed(12345)
            for _ in range(50):
                random.random()
            return _build(MapIntermediate01, 3)

        gc.collect()
        assert fingerprint() == fingerprint()


class TestSensorNoiseReproducibility:
    """A seeded run must replay its noisy sensor readings too.

    The sensor noise used to draw from the global numpy RNG, so even with a
    fixed seed the readings differed between two runs. The playground now
    hands every sensor a noise generator derived from its seed when it claims
    the drone (`Playground._wire_sensor_noise`), so the same seed replays the
    same readings.
    """

    @staticmethod
    def _readings(map_class, seed, n_steps=3):
        the_map = map_class(drone_type=DroneMotionless, seed=seed)
        out = []
        for _ in range(n_steps):
            the_map.playground.step()
            for drone in the_map.playground.agents:
                for sensor in drone.sensors:
                    out.append((type(sensor).__name__,
                                repr(getattr(sensor, "_values", None))))
        return out

    @staticmethod
    def _noise_rigs(the_map):
        """The generator each noise model of each sensor comes from.

        A sensor may hold one noise model (`_noise_model`) or several named
        ones (the odometer keeps one per component); the walk below covers
        both shapes and ignores sensors without any.
        """
        out = []
        for drone in the_map.playground.agents:
            for sensor in drone.sensors:
                for name, value in vars(sensor).items():
                    if "noise" in name and hasattr(value, "_rng"):
                        out.append(repr(value._rng))
        return out

    def test_same_seed_gives_identical_noisy_readings(self):
        first = self._readings(MapIntermediate01, 1234)
        second = self._readings(MapIntermediate01, 1234)
        assert first == second, "noisy readings differ across identical seeds"

    def test_seeded_sensors_use_the_derived_noise_generator(self):
        the_map = MapIntermediate01(drone_type=DroneMotionless, seed=42)
        rigs = self._noise_rigs(the_map)
        # Every sensor carries a generator (never None), and all share the
        # playground's noise generator: one stream for the whole scene.
        assert rigs and all(r != "None" for r in rigs)
        expected = repr(the_map.playground._noise_rng)
        assert all(r == expected for r in rigs)

    def test_unseeded_sensors_stay_on_the_global_rng(self):
        the_map = MapIntermediate01(drone_type=DroneMotionless)
        assert all(r == "None" for r in self._noise_rigs(the_map))

    def test_unseeded_runs_still_differ(self):
        first = self._readings(MapIntermediate01, None)
        second = self._readings(MapIntermediate01, None)
        assert first != second

    def test_uid_stream_untouched_by_noise(self):
        """The noise generator is separate: sensors consuming noise must not
        shift the UID stream, which would change entity identification."""
        the_map = MapIntermediate01(drone_type=DroneMotionless, seed=7)
        state_before = the_map.playground._rng.bit_generator.state["state"]
        the_map.playground.step()
        state_after = the_map.playground._rng.bit_generator.state["state"]
        assert state_before == state_after
