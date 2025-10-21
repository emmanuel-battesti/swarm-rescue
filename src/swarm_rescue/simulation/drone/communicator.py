from __future__ import annotations

from typing import Any, List, Optional, Tuple

from swarm_rescue.simulation.drone.pocket_device import PocketDevice

Message = Any

COMM_COLOR = (123, 134, 13)


class Communicator(PocketDevice):
    """
    Device for communication between agents, allowing message transmission within a certain range.
    """

    def __init__(
            self,
            transmission_range: Optional[float] = None,
    ):
        """
        By default, Communicator has infinite range and infinite receiver capacity.
        However, it can only send one message at a time.

        Args:
            transmission_range (Optional[float]): Communication range in pixels. None means infinite.
        """

        super().__init__(color=COMM_COLOR)

        self._transmission_range = transmission_range

        self._comms_in_range: List[Communicator] = []
        self._received_messages: List[Tuple[Communicator, Message]] = []

    def pre_step(self) -> None:
        """
        Prepare communicator for a new simulation step.
        """
        super().pre_step()
        self.update_list_comms_in_range()
        self._received_messages = []

    def reset(self) -> None:
        """
        Reset communicator state.
        """
        self.pre_step()
        super().reset()

    @property
    def transmission_range(self) -> Optional[float]:
        """
        Returns the communication range in pixels, or None if infinite.
        """
        return self._transmission_range

    def update_list_comms_in_range(self) -> None:
        """
        Update the list of communicators in range.
        """
        assert self._playground

        comms = []
        for agent in self._playground.agents:
            comms += agent.communicators

        valid_comms = [com for com in comms if com is not self]

        self._comms_in_range.clear()
        for comm in valid_comms:
            if self.in_transmission_range(comm):
                self._comms_in_range.append(comm)

    @property
    def comms_in_range(self) -> List[Communicator]:
        """
        Returns the list of communicators currently in range.
        """
        return self._comms_in_range

    @property
    def received_messages(self) -> List[Tuple[Communicator, Message]]:
        """
        Returns the list of received messages as (sender, message) tuples.
        """
        return self._received_messages

    def in_transmission_range(self, comm: Communicator) -> bool:
        """
        Check if another communicator is within transmission range.

        Args:
            comm (Communicator): The other communicator.

        Returns:
            bool: True if in range, False otherwise.
        """
        dist = comm.position.get_distance(self.position) # type: ignore[arg-type]

        # If both have infinite range:
        if not (comm.transmission_range or self._transmission_range):
            return True

        # If only one has infinite range:
        if (not comm.transmission_range) and self._transmission_range:
            if dist < self._transmission_range:
                return True

        elif comm.transmission_range and (not self._transmission_range):
            if dist < comm.transmission_range:
                return True

        elif dist < comm.transmission_range and dist < self._transmission_range:
            return True

        return False

    def send(self, msg: Message, ) -> Optional[Message]:
        """
        Send a message if the communicator is enabled.

        Args:
            msg (Message): The message to send.

        Returns:
            Optional[Message]: The message if sent, None if disabled.
        """
        if self._disabled:
            return None

        return msg

    def receive(self, sender: Communicator, msg: Message) -> Optional[Message]:
        """
        Receive a message from another communicator.

        Args:
            sender (Communicator): The sender.
            msg (Message): The message.

        Returns:
            Optional[Message]: The message if received, None otherwise.
        """
        if self._disabled or sender is self:
            return None

        if self.in_transmission_range(sender):
            self._received_messages.append((sender, msg))
            return msg

        return None
