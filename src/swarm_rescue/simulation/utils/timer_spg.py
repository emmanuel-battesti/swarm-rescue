from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import Playground


class Timer(ABC):
    """
    Abstract base class for timers in the simulation.
    """

    def __init__(self):
        """
        Initialize the Timer.
        """
        self._running: bool = False
        self._time: int = 0
        self._tic: bool = False
        self._playground: Optional["Playground"] = None

    @property
    def tic(self) -> bool:
        """
        Returns whether the timer has ticked.

        Returns:
            bool: True if ticked, False otherwise.
        """
        return self._tic

    def start(self) -> None:
        """
        Start the timer.
        """
        self._running = True

    def stop(self) -> None:
        """
        Stop the timer.
        """
        self._running = False

    def step(self) -> None:
        """
        Advance the timer by one step.
        """
        if self._running:
            self._time += 1

    def reset(self) -> None:
        """
        Reset the timer.
        """
        self.stop()
        self._time = 0

    @property
    def playground(self) -> Optional["Playground"]:
        """
        Returns the playground associated with the timer.

        Returns:
            Optional[Playground]: The playground.
        """
        return self._playground

    @playground.setter
    def playground(self, pg: Playground) -> None:
        """
        Set the playground for the timer.

        Args:
            pg (Playground): The playground.
        """
        self._playground = pg

    @property
    def in_playground(self) -> bool:
        """
        Returns whether the timer is associated with a playground.

        Returns:
            bool: True if in playground, False otherwise.
        """
        return bool(self._playground)


class CountDownTimer(Timer):
    """
    Timer that counts down for a specified duration and ticks when done.
    """

    def __init__(self, duration: int):
        """
        Initialize the CountDownTimer.

        Args:
            duration (int): Duration to count down.
        """
        super().__init__()
        self._duration: int = duration

    def step(self) -> None:
        """
        Advance the timer by one step and tick if duration reached.
        """
        super().step()

        if self._tic:
            self._tic = False

        if self._time == self._duration:
            self.reset()
            self._tic = True


class PeriodicTimer(Timer):
    """
    Timer that ticks periodically with specified durations.
    """

    def __init__(self, durations: Union[List[int], int, Tuple[int, ...]]):
        """
        Initialize the PeriodicTimer.

        Args:
            durations (Union[List[int], int, Tuple[int, ...]]): List or single duration for periods.
        """
        if isinstance(durations, int):
            durations = [durations]

        assert isinstance(durations, (list, tuple))

        self._durations: Union[List[int], Tuple[int, ...]] = durations
        self._current_duration: int = self._durations[0]
        self._index_duration: int = 0

        super().__init__()

    def reset(self) -> None:
        """
        Reset the periodic timer.
        """
        super().reset()
        self._index_duration = 0
        self._current_duration = self._durations[0]
        self._tic = False
        self.start()

    def step(self) -> None:
        """
        Advance the timer by one step and tick if current period reached.
        """
        super().step()

        if self.tic:
            self._tic = False

        if self._time == self._current_duration:
            self._index_duration = (self._index_duration + 1) % len(self._durations)
            self._current_duration = self._durations[self._index_duration]

            self._time = 0
            self._tic = True

