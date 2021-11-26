from pygame.time import Clock


class FpsDisplay:
    def __init__(self, period_display=1, fps_limit=1000):
        self._period_display = period_display
        self._clock = Clock()
        self._counter = 0
        self._initialized = False

        self.fps_limit = fps_limit
        self.mean_fps = 0

    def reset(self):
        self._counter = 0
        self._initialized = False
        self.mean_fps = 0

    def update(self):
        self._counter += 1
        fps = self._clock.get_fps()

        if not self._initialized and fps != 0.0:
            self._initialized = True
            self.mean_fps = fps

        if self._initialized:
            alpha = 0.99
            self.mean_fps = alpha * self.mean_fps + (1 - alpha) * fps

        step_display = int(fps * self._period_display)

        if step_display != 0 and self._counter % step_display == 0:
            print("FPS: {:.2f}, mean FPS: {:.2f}".format(fps, self.mean_fps))

        self._clock.tick(self.fps_limit)
