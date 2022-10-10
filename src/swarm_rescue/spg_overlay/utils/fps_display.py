from timeit import default_timer as timer


class FpsDisplay:
    def __init__(self, period_display=1):
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
        self._counter = 0
        self._initialized = False
        self.mean_fps = 0

    def update(self, display: bool = True):
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
