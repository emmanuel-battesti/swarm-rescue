"""
The order of the phases in a simulation step is a contract.

Reordering them does not raise: the run still completes, still produces a score,
and is simply wrong in a way nobody notices until the results are odd. So the
order is pinned here rather than left to be inferred from the source.

These tests drive `SimulationStepper` against a stub world, which is only
possible because the loop no longer lives inside `Playground` -- a stub cannot
build a window.
"""

import pathlib
import sys

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.simulation_stepper import SimulationStepper


class StubElement:
    """An element that only reports when it is called."""

    def __init__(self, log):
        self._log = log

    def pre_step(self):
        self._log.append("element.pre_step")

    def post_step(self):
        self._log.append("element.post_step")


class StubAgent:
    """An agent that only reports when it is called."""

    def __init__(self, log, name="agent"):
        self._log = log
        self.name = name
        self.reward = 1.5
        self.removed = False
        self.commands = None
        self.communicators = []

    def pre_step(self):
        self._log.append(f"{self.name}.pre_step")

    def post_step(self):
        self._log.append(f"{self.name}.post_step")

    def receive_commands(self, commands):
        self.commands = commands

    def apply_commands(self):
        self._log.append(f"{self.name}.apply_commands")

    def compute_observations(self):
        self._log.append(f"{self.name}.compute_observations")


class StubSpace:
    def __init__(self, log):
        self._log = log

    def step(self, dt):
        self._log.append(f"space.step({dt:.4f})")


class StubRayCompute:
    def __init__(self, log):
        self._log = log

    def update_sensors(self):
        self._log.append("ray_compute.update_sensors")


class StubPlayground:
    """
    The minimum a stepper needs: a world to iterate and a space to advance.

    Everything the stepper reads is here, and nothing here needs OpenGL.
    """

    def __init__(self, log, with_ray_compute=True):
        self._log = log
        self._agents = [StubAgent(log, "a"), StubAgent(log, "b")]
        self.elements = [StubElement(log)]
        self.space = StubSpace(log)
        self._ray_compute = StubRayCompute(log) if with_ray_compute else None
        self._timestep = 0

    @property
    def agents(self):
        return self._agents

    def _agents_with_removals(self):
        return self._agents


def _run(log, **kwargs):
    """Run one step with an explicit substep count, so the log is predictable."""
    kwargs.setdefault("pymunk_steps", 2)
    playground = StubPlayground(log)
    stepper = SimulationStepper(playground)
    result = stepper.step(**kwargs)
    return playground, result


class TestPhaseOrder:
    """The order below is the contract; each phase has a stated reason."""

    def test_the_full_order(self):
        log = []
        _run(log)

        assert log == [
            "element.pre_step",
            "a.pre_step",
            "b.pre_step",
            # physics, once per substep
            "space.step(0.5000)",
            "space.step(0.5000)",
            # sensors read the post-collision world
            "ray_compute.update_sensors",
            "a.compute_observations",
            "b.compute_observations",
            "element.post_step",
            "a.post_step",
            "b.post_step",
        ], f"unexpected step order: {log}"

    def test_observations_come_after_the_physics(self):
        """
        A sensor must not report a collision that has not been resolved yet.

        If these two swap, the lidar can see through a wall it just hit.
        """
        log = []
        _run(log)

        assert log.index("ray_compute.update_sensors") > log.index("space.step(0.5000)")

    def test_post_step_comes_after_the_observations(self):
        """An agent's post_step must see the same world its sensors reported."""
        log = []
        _run(log)

        assert log.index("a.post_step") > log.index("a.compute_observations")

    def test_commands_are_applied_before_the_physics(self):
        """A command has to reach the body before pymunk moves it."""
        log = []
        playground = StubPlayground(log)
        stepper = SimulationStepper(playground)
        commands = {agent: {"forward": 1.0} for agent in playground._agents}

        stepper.step(all_commands=commands, pymunk_steps=2)

        assert log.index("a.apply_commands") < log.index("space.step(0.5000)")

    def test_every_command_is_received_before_any_is_applied(self):
        """
        All drones must be told what to do before any of them acts.

        Applying as we go would let the first agent in the dictionary react
        before the last one has even been given its command, which makes the
        outcome depend on dictionary ordering.
        """
        log = []
        playground = StubPlayground(log)
        stepper = SimulationStepper(playground)

        commands = {
            playground._agents[0]: {"forward": 1.0},
            playground._agents[1]: {"forward": -1.0},
        }
        stepper.step(all_commands=commands)

        assert playground._agents[0].commands == {"forward": 1.0}
        assert playground._agents[1].commands == {"forward": -1.0}
        assert log.count("a.apply_commands") == 1
        assert log.count("b.apply_commands") == 1


class TestStepAccounting:
    def test_the_timestep_advances_by_one(self):
        log = []
        playground, _ = _run(log)

        assert playground._timestep == 1

    def test_pymunk_steps_controls_the_substeps_not_the_timestep(self):
        """Micro-steps make the physics smoother, not the clock faster."""
        log = []
        playground, _ = _run(log, pymunk_steps=5)

        assert playground._timestep == 1
        assert sum(1 for entry in log if entry.startswith("space.step")) == 5

    def test_the_substeps_sum_to_one_unit_of_time(self):
        """The physics advances by the same amount whatever the substep count."""
        log = []
        _run(log, pymunk_steps=4)

        steps = [float(entry[len("space.step("):-1]) for entry in log
                 if entry.startswith("space.step")]
        assert sum(steps) == 1.0


class TestRewards:
    def test_the_reward_of_every_agent_is_reported(self):
        log = []
        playground, (_, rewards) = _run(log)

        assert set(rewards) == set(playground._agents)
        assert all(value == 1.5 for value in rewards.values())

    def test_rewards_are_reported_even_without_commands(self):
        """A step with no commands is still a step."""
        log = []
        _, (_, rewards) = _run(log)

        assert len(rewards) == 2


class TestMissingRayCompute:
    def test_a_world_without_ray_sensors_still_steps(self):
        """The CPU-only and no-sensor paths must not depend on the sensors."""
        log = []
        playground = StubPlayground(log, with_ray_compute=False)
        SimulationStepper(playground).step()

        assert "ray_compute.update_sensors" not in log
        assert "a.compute_observations" in log
        assert playground._timestep == 1
