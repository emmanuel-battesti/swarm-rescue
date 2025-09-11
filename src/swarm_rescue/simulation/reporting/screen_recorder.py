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

    def __init__(self, width: int, height: int, fps: int, out_file: str):
        """
        Initialize the recorder with parameters of the view.

        Args:
            width (int): Width of the view to capture.
            height (int): Height of the view to capture.
            fps (int): Frames per second.
            out_file (str): Output file to save the recording.
        """

        if out_file is None:
            self.video = None
            return

        self._out_file = out_file

        print("Initializing ScreenRecorder with parameters : width:{}, "
              "height:{}, fps:{}.".format(width, height, fps))

        # define the codec and create a video writer object
        four_cc = cv2.VideoWriter_fourcc(*'XVID')
        self.video = cv2.VideoWriter(out_file, four_cc, float(fps),
                                     (width, height))

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