# timer.py

import time
from enum import Enum


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class StateTimer(Enum):
    stopped = 0
    running = 1
    pause = 2


class Timer:
    """
    This class provides precise timer functionalities and a pause function.
    The Timer class provides precise timer functionalities and a pause function. It allows users to start, stop,
    restart, and pause the timer, and also provides methods to get the elapsed time in different units. The class
    uses the time module to measure the time and the enum module to define the timer states.

    Example Usage
        # Create a timer object
        timer = Timer()

        # Start the timer
        timer.start()

        # Do some processing
        ...

        # Pause the timer
        timer.pause_on()

        # Do some more processing
        ...

        # Resume the timer
        timer.pause_off()

        # Stop the timer and print the elapsed time
        timer.stop()
        timer.print("Processing")

        # Restart the timer
        timer.restart()

        # Stop the timer and print the elapsed time again
        timer.stop()
        timer.print("Processing")

    Main functionalities:
        Start a new timer
        Stop the timer and report the elapsed time
        Pause and resume the timer
        Restart the timer
        Get the elapsed time in seconds and milliseconds

    Attributes:
        _start_time: Stores the start time of the timer.
        _stop_time: Stores the stop time of the timer.
        _start_time_pause: Stores the start time of a pause.
        _state: Stores the current state of the timer.
        _durationAllPauses: Stores the total duration of all pauses.
        _durationBeforePause: Stores the duration before a pause.
    """

    def __init__(self, start_now: bool = False):
        self._start_time: float = 0
        self._stop_time: float = 0

        self._start_time_pause: float = 0

        self._state = StateTimer.stopped
        self._durationAllPauses: float = 0.0
        self._durationBeforePause: float = 0.0

        if start_now:
            self.start()

    def start(self):
        """Start a new timer"""

        if self._state is not StateTimer.stopped:
            return

        self._state = StateTimer.running
        self._durationAllPauses = 0
        self._start_time = time.perf_counter()

    def restart(self):
        """ Restarts the timer by stopping and starting it again"""
        self.stop()
        self.start()

    def stop(self):
        """Stops the timer and calculates the elapsed time."""
        if self._state is StateTimer.stopped:
            return
            # raise TimerError(f"Timer is not running. Use .start() to start it")

        self.pause_off()
        self._state = StateTimer.stopped

        self._stop_time = time.perf_counter()
        # print(f"Elapsed time: {elapsed_time:0.4f} seconds")

    def pause_on(self):
        """Pauses the timer and records the duration before the pause."""
        if self._state is not StateTimer.running:
            return

        self._state = StateTimer.pause

        self._durationBeforePause = self.get_elapsed_time()
        self._start_time_pause = time.perf_counter()

    def pause_off(self):
        """Resumes the timer and calculates the duration of the pause."""
        if self._state is not StateTimer.pause:
            return

        self._state = StateTimer.running

        time_stop = time.perf_counter()
        duration_pause = time_stop - self._start_time_pause
        self._durationAllPauses += duration_pause

    def get_elapsed_time(self):
        """Returns the elapsed time in seconds, taking into account any pauses."""
        if self._state is StateTimer.pause:
            return self._durationBeforePause

        time_stop = time.perf_counter()

        if self._state is StateTimer.stopped:
            time_stop = self._stop_time

        duration = time_stop - self._start_time

        return duration - self._durationAllPauses

    def get_elapsed_time_in_milliseconds(self):
        """Returns the elapsed time in milliseconds."""
        return self.get_elapsed_time() * 1000.0

    def print(self, txt):
        """Prints the processed text and the elapsed time in milliseconds, seconds, and minutes."""
        print(" * Processed {} in {} ms, {} s or {} min".format(txt,
                                                                self.get_elapsed_time_in_milliseconds(),
                                                                self.get_elapsed_time(),
                                                                self.get_elapsed_time() / 60))

    def get_state_str(self, ):
        """Returns a string representation of the timer state, for debug."""
        if self._state is StateTimer.stopped:
            state_str = "stopped"
        elif self._state is StateTimer.running:
            state_str = "running"
        elif self._state is StateTimer.pause:
            state_str = "pause"
        else:
            state_str = "error"

        return state_str
