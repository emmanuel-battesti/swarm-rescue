from timeit import default_timer as timer


class FpsDisplay:
    """
    The FpsDisplay class is used to calculate and display frames per second (FPS) information. It keeps track
    of the mean FPS, current FPS, and smooth FPS values. The class provides methods to update the FPS values and reset
    the counter. It also has a method to display the FPS information at a specified interval.

    Example Usage:
        # Create an instance of FpsDisplay with a display period of 1 second
        fps_display = FpsDisplay(period_display=1)

        # Update the FPS values
        fps_display.update()

        # Display the FPS information
        fps_display.update(display=True)

    Main functionalities:
        Calculate and display frames per second (FPS) information
        Keep track of mean FPS, current FPS, and smooth FPS values
        Reset the counter

    Attributes:
        mean_fps: Mean FPS value.
        fps: Current FPS value.
        smooth_fps: Smoothed FPS value.
        start: Start time of the FPS calculation.
        t1: Previous time of the FPS calculation.
        t2: Current time of the FPS calculation.
    """

    def __init__(self, period_display=1):
        """
        Initializes the FpsDisplay object
        with the specified display period (default is 1 second).
        """
        self._period_display = period_display
        self._counter = 0
        self._initialized = False

        self.mean_fps = 0
        self.fps = 0
        self.smooth_fps = 0

        self.start = timer()
        self.t1 = self.start
        self.t2 = self.start

    def reset(self):
        """
        Resets the counter and mean FPS value.
        """
        self._counter = 0
        self._initialized = False
        self.mean_fps = 0

    def update(self, display: bool = True):
        """
        Updates the FPS values and displays the FPS information if specified. If not initialized, it initializes
        the necessary variables.
        """
        if not self._initialized:
            self._initialized = True
            self.start = timer()
            self.t1 = self.start
            self.t2 = self.start
            self._counter = 0
            self.mean_fps = 0
            self.fps = 0
            self.smooth_fps = 0
            return

        self._counter += 1
        self.t1 = self.t2
        self.t2 = timer()
        self.mean_fps = self._counter / (self.t2 - self.start)
        self.fps = 1 / (self.t2 - self.t1)
        if self._counter == 1:
            self.smooth_fps = self.fps

        if self._initialized:
            alpha = 0.95
            self.smooth_fps = alpha * self.smooth_fps + (1 - alpha) * self.fps

        step_display = int(self.smooth_fps * self._period_display)

        if display and step_display != 0 and self._counter % step_display == 0:
            print("FPS: {:.2f}, mean FPS: {:.2f},  smooth FPS: {:.2f}".format(self.fps, self.mean_fps, self.smooth_fps))
