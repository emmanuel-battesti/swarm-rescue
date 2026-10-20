from typing import Optional, Tuple

import cv2

from swarm_rescue.simulation.gui_map.top_down_view import TopDownView


class ScreenRecorder:
    """
    Used to record a view and save it to a video file.
    It initializes the recorder with the parameters of the
    view, captures frames from the view, and stops the recording when
    needed.

    Example Usage
        # Create a ScreenRecorder object with the desired parameters
        recorder = ScreenRecorder(width=640, height=480, fps=30,
                                  out_file='output.avi')

        # Call the capture_frame method for each frame to record
        recorder.capture_frame(gui)

        # Stop the recording
        recorder.end_recording()
    """

    def __init__(self, width: int, height: int, fps: int,
                 out_file: Optional[str]):
        """
        Initialize the recorder with parameters of the view.

        Args:
            width (int): Width of the view to capture.
            height (int): Height of the view to capture.
            fps (int): Frames per second.
            out_file (str): Output file to save the recording.
        """

        # Declared up-front so the type checker knows them even when the
        # recording is disabled (``out_file`` is None).
        self.video: Optional[cv2.VideoWriter] = None
        self._size: Optional[Tuple[int, int]] = None
        self._out_file: Optional[str] = None

        if out_file is None:
            return

        self._out_file = out_file
        self._size = (int(width), int(height))

        print("Initializing ScreenRecorder with parameters: width:{}, "
              "height:{}, fps:{}.".format(width, height, fps))

        # define the codec and create a video writer object
        four_cc = cv2.VideoWriter.fourcc(*'XVID')
        self.video = cv2.VideoWriter(out_file, four_cc, float(fps),
                                     (self._size[0], self._size[1]))

    def capture_frame(self, gui: TopDownView) -> None:
        """
        Call this method every frame to capture the current view.

        Args:
            gui (TopDownView): View to capture.
        """

        if self.video is None:
            return

        gui.update_and_draw_in_framebuffer()
        # img_capture have float values between 0 and 1
        # The image should be flip and the color channel permuted
        img_capture = cv2.flip(gui.get_np_img(), 0)
        img_capture = cv2.cvtColor(img_capture, cv2.COLOR_RGB2BGR)

        # Ensure frame size matches the VideoWriter expectation
        h, w = img_capture.shape[:2]
        if self._size is not None and (w, h) != self._size:
            # Resize to expected size to avoid FFmpeg write errors due to size mismatch
            # This can happen if auto-resize reduced the window size at initialization
            # Use appropriate interpolation: INTER_AREA for downscaling, INTER_LINEAR for upscaling
            if w > self._size[0] or h > self._size[1]:
                # Downscaling: use INTER_AREA (best quality for shrinking)
                interpolation = cv2.INTER_AREA
            else:
                # Upscaling: use INTER_LINEAR (faster and good enough for enlarging)
                interpolation = cv2.INTER_LINEAR
            img_capture = cv2.resize(img_capture, self._size, interpolation=interpolation)

        # write the frame
        self.video.write(img_capture)

    def end_recording(self) -> None:
        """
        Call this method to stop recording and save the video.
        """
        if self.video is None:
            return

        # stop recording
        self.video.release()
        print("\n")
        print("Output of the screen recording saved to {}."
              .format(self._out_file))

# References
#   For more tutorials on cv2.VideoWriter, go to:
#   - https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html#display-video
#   - https://medium.com/@enriqueav/how-to-create-video-animations-using-python-and-opencv-881b18e41397
