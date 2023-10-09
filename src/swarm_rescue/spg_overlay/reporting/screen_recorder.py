import cv2
from spg.view import TopDownView


class ScreenRecorder:
    """
        The ScreenRecorder class is used to record a view and save it to a video file. It initializes the recorder
        with the parameters of the view, captures frames from the view, and stops the recording when needed.

        Example Usage
            # Create a ScreenRecorder object with the desired parameters
            recorder = ScreenRecorder(width=640, height=480, fps=30, out_file='output.avi')

            # Call the capture_frame method for each frame to record
            recorder.capture_frame(gui)

            # Stop the recording
            recorder.end_recording()
    """

    def __init__(self, width, height, fps, out_file):
        """
        Initialize the recorder with parameters of the view.
        :param width: Width of the view to capture
        :param height: Height of the view to capture
        :param fps: Frames per second
        :param out_file: Output file to save the recording
        """

        if out_file is None:
            self.video = None
            return

        self._out_file = out_file

        print("Initializing ScreenRecorder with parameters : width:{}, height:{}, fps:{}.".format(width, height, fps))

        # define the codec and create a video writer object
        four_cc = cv2.VideoWriter_fourcc(*'XVID')
        self.video = cv2.VideoWriter(out_file, four_cc, float(fps), (width, height))

    def capture_frame(self, gui: TopDownView):
        """
         Call this method every frame.
        :param gui: view to capture
        :return: None
        """

        if self.video is None:
            return

        gui.update()
        # img_capture have float values between 0 and 1
        # The image should be flip and the color channel permuted
        img_capture = cv2.flip(gui.get_np_img(), 0)
        img_capture = cv2.cvtColor(img_capture, cv2.COLOR_RGB2BGR)

        # write the frame
        self.video.write(img_capture)

    def end_recording(self):
        """
        Call this method to stop recording.
        :return: None
        """
        if self.video is None:
            return

        # stop recording
        self.video.release()
        print("Output of the screen recording saved to {}.".format(self._out_file))

# References
#   For more tutorials on cv2.VideoWriter, go to:
#   - https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html#display-video
#   - https://medium.com/@enriqueav/how-to-create-video-animations-using-python-and-opencv-881b18e41397
