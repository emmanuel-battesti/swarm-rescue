"""
The simulation loop, run by `Playground`.

It drives the physics, exchanges the messages, and refreshes the sensors. None
of it touches a window, a framebuffer or a camera, so the loop can run, and be
tested, without one.

Keeping it in a single readable function states the ordering once, and lets a
test pin it by recording the calls instead of having to infer it from the
source.

The stepper holds a reference to its playground and reads the world from it.
That is deliberate: passing eight arguments to every helper would move the
coupling, not remove it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.communicator import Communicator
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.utils.definitions import PYMUNK_STEPS

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import (
        AllSentMessagesDict,
        Playground,
    )


class SimulationStepper:
    """
    Runs one timestep of the simulation.

    The order of the phases is a contract, and the reason for each is given
    where it happens. Getting it wrong does not crash: it produces a run that
    looks plausible and is subtly wrong, which is the worst kind of defect in a
    competition.
    """

    def __init__(self, playground: Playground) -> None:
        """
        Args:
            playground (Playground): The world this stepper advances.
        """
        self._playground = playground

    def step(self,
             all_commands: Optional[Dict[Agent, CommandsDict]] = None,
             all_messages: Optional[AllSentMessagesDict] = None,
             pymunk_steps: int = PYMUNK_STEPS,
             ):
        """
        Advance the simulation by one timestep.

        Args:
            all_commands (Optional[Dict[Agent, CommandsDict]]): Commands for agents.
            all_messages (Optional[AllSentMessagesDict]): Messages for communicators.
            pymunk_steps (int): Number of steps for the pymunk physics engine to run.

        Returns:
            tuple: (messages, rewards)

        Notes:
            pymunk_steps only influences the micro-steps that the physical
            engine takes to render movement and collisions. From an external
            point of view, one unit of time passes regardless of its value.
        """
        playground = self._playground

        self._pre_step()

        self._apply_commands(all_commands)

        for _ in range(pymunk_steps):
            playground.space.step(1.0 / pymunk_steps)

        self._compute_observations()

        self._post_step()

        rewards = {agent: agent.reward for agent in playground._agents_with_removals()}

        messages = None
        if all_messages:
            messages = self._transmit_messages(all_messages)

        playground._timestep += 1

        return messages, rewards

    def _pre_step(self) -> None:
        """
        Announce the start of the step to every element and agent.

        Elements come first: a drone reacting to a moving wall must not see the
        wall's new position before the wall has moved.
        """
        playground = self._playground

        for element in playground.elements:
            element.pre_step()

        for agent in playground.agents:
            agent.pre_step()

    def _post_step(self) -> None:
        """
        Announce the end of the physics phase, after the collisions resolved.

        This runs *after* `_compute_observations` so that an agent's
        `post_step()` sees the same world its sensors just reported.
        """
        playground = self._playground

        for element in playground.elements:
            element.post_step()

        for agent in playground.agents:
            agent.post_step()

    def _apply_commands(self,
                        all_commands: Optional[Dict[Agent, CommandsDict]] = None,
                        ) -> None:
        """
        Collect the commands, then let every agent apply its own.

        Args:
            all_commands (Optional[Dict[Agent, CommandsDict]]): Commands for agents.
        """
        if not all_commands:
            return

        for agent, commands_dict in all_commands.items():
            agent.receive_commands(commands_dict)

        for agent in self._playground._agents_with_removals():
            agent.apply_commands()

    def _compute_observations(self) -> None:
        """
        Refresh the ray sensors once, then let every agent read its own.

        The ray compute is driven once for the whole scene rather than once per
        agent: it renders every entity into a single offscreen image, so doing
        it per drone would scale the cost with the fleet size for no gain.
        """
        playground = self._playground

        if playground._ray_compute:
            playground._ray_compute.update_sensors()

        for agent in playground.agents:
            agent.compute_observations()

    def _transmit_messages(self, all_messages: Optional[AllSentMessagesDict] = None):
        """
        Deliver the messages every drone asked to send, and collect replies.

        Args:
            all_messages (Optional[AllSentMessagesDict]): Messages to transmit.

        Returns:
            dict: Received messages, per agent and per communicator.
        """
        playground = self._playground
        all_messages = all_messages or {}

        msgs = {agent: {} for agent in playground.agents}

        all_sent_messages = [
            (agent, comm_source, target)
            for agent, comms_dict in all_messages.items()
            for comm_source, target in comms_dict.items()
        ]

        for agent, comm_source, target in all_sent_messages:

            assert comm_source.agent is agent

            comm_target, message = target
            msg = comm_source.send(message)

            if not msg:
                continue

            if isinstance(comm_target, list):
                for targ in comm_target:
                    assert isinstance(targ, Communicator)
                    received_msg = targ.receive(comm_source, msg)

                    if received_msg:
                        msgs[targ.agent][targ] = (comm_source, received_msg)

            elif isinstance(comm_target, Communicator):
                received_msg = comm_target.receive(comm_source, msg)

                if received_msg:
                    msgs[comm_target.agent][comm_target] = (comm_source, received_msg)

            elif comm_target is None:
                # Broadcast: every communicator in range hears it, including
                # those the sender did not know about.
                for agent2 in playground.agents:
                    for comm in agent2.communicators:
                        received_msg = comm.receive(comm_source, msg)
                        if received_msg:
                            msgs[comm.agent][comm] = (comm_source, received_msg)

            else:
                raise ValueError(
                    f"A message target must be a Communicator, a list of them, "
                    f"or None for a broadcast; got {type(comm_target).__name__}."
                )

        return msgs
