import arcade
import time
from typing import Optional, Tuple, List, Dict, Union, Type
import cv2

from spg.agent.controller.controller import Command, Controller
from spg.playground import Playground
from spg.playground.playground import SentMessagesDict
from spg.view import TopDownView

from spg_overlay.utils.constants import FRAME_RATE
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.keyboard_controller import KeyboardController
from spg_overlay.utils.fps_display import FpsDisplay
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.mouse_measure import MouseMeasure
from spg_overlay.utils.screen_recorder import ScreenRecorder
from spg_overlay.utils.visu_noises import VisuNoises


class GuiSR(TopDownView):
    def __init__(
            self,
            playground: Playground,
            the_map: MapAbstract,
            size: Optional[Tuple[int, int]] = None,
            center: Tuple[float, float] = (0, 0),
            zoom: float = 1,
            display_uid: bool = False,
            draw_transparent: bool = False,
            draw_interactive: bool = False,
            draw_zone: bool = True,
            draw_lidar: bool = False,
            draw_semantic: bool = False,
            draw_touch: bool = False,
            print_rewards: bool = False,
            print_messages: bool = False,
            use_keyboard: bool = False,
            use_mouse_measure: bool = False,
            enable_visu_noises: bool = False,
            filename_video_capture: str = None
    ) -> None:
        super().__init__(
            playground,
            size,
            center,
            zoom,
            display_uid,
            draw_transparent,
            draw_interactive,
            draw_zone,
        )

        self._playground.window.set_size(*self._size)
        self._playground.window.set_visible(True)

        self._the_map = the_map
        self._drones = self._the_map.drones
        self._number_drones = self._the_map.number_drones

        self._real_time_limit = self._the_map.real_time_limit
        if self._real_time_limit is None:
            self._real_time_limit = 100000000

        self._drones_commands: Union[Dict[DroneAbstract, Dict[Union[str, Controller], Command]], Type[None]] = None
        if self._drones:
            self._drones_commands = {}

        self._messages = None
        self._print_rewards = print_rewards
        self._print_messages = print_messages

        self._playground.window.on_draw = self.on_draw
        self._playground.window.on_update = self.on_update
        self._playground.window.on_key_press = self.on_key_press
        self._playground.window.on_key_release = self.on_key_release
        self._playground.window.on_mouse_motion = self.on_mouse_motion
        self._playground.window.on_mouse_press = self.on_mouse_press
        self._playground.window.on_mouse_release = self.on_mouse_release
        self._playground.window.set_update_rate(FRAME_RATE)

        self._draw_lidar = draw_lidar
        self._draw_semantic = draw_semantic
        self._draw_touch = draw_touch
        self._use_keyboard = use_keyboard
        self._use_mouse_measure = use_mouse_measure
        self._enable_visu_noises = enable_visu_noises

        # 'number_wounded_persons' is the number of wounded persons that should be retrieved by the drones.
        self._total_number_wounded_persons = self._the_map.number_wounded_persons
        self._rescued_number = 0
        self._rescued_all_time_step = 0
        self._elapsed_time = 0
        self._start_real_time = time.time()
        self._real_time_limit_reached = False
        self._real_time_elapsed = 0

        self._last_image = None
        self._terminate = False

        self.fps_display = FpsDisplay(period_display=2)
        self._keyboardController = KeyboardController()
        self._mouse_measure = MouseMeasure(playground_size=playground.size)
        self._visu_noises = VisuNoises(playground_size=playground.size, drones=self._drones)

        self.recorder = ScreenRecorder(self._size[0], self._size[1], fps=30, out_file=filename_video_capture)

    def run(self):
        self._playground.window.run()

    def on_draw(self):
        self._playground.window.clear()
        self._fbo.use()
        self.draw()

    def on_update(self, delta_time):
        self._elapsed_time += 1

        if self._elapsed_time < 2:
            self._playground.step(commands=self._drones_commands, messages=self._messages)
            return

        self._the_map.explored_map.update(self._drones)

        # COMPUTE ALL THE MESSAGES
        self._messages = self.collect_all_messages(self._drones)

        # COMPUTE COMMANDS
        for i in range(self._number_drones):
            command = self._drones[i].control()
            if self._use_keyboard and i == 0:
                command = self._keyboardController.control()

            self._drones_commands[self._drones[i]] = command

        if self._drones:
            self._drones[0].display()

        self._playground.step(commands=self._drones_commands, messages=self._messages)

        self._visu_noises.update(enable=self._enable_visu_noises)
        # self._the_map.explored_map.display()

        # REWARDS
        new_reward = 0
        for i in range(self._number_drones):
            new_reward += self._drones[i].reward

        if new_reward != 0:
            self._rescued_number += new_reward

        if self._rescued_number == self._total_number_wounded_persons and self._rescued_all_time_step == 0:
            self._rescued_all_time_step = self._elapsed_time

        end_real_time = time.time()
        self._real_time_elapsed = (end_real_time - self._start_real_time)
        if self._real_time_elapsed > self._real_time_limit:
            self._real_time_elapsed = self._real_time_limit
            self._real_time_limit_reached = True
            self._terminate = True

        if self._print_rewards:
            for agent in self._playground.agents:
                if agent.reward != 0:
                    print(agent.reward)

        if self._print_messages:
            for drone in self._playground.agents:
                for comm in drone.communicators:
                    for _, msg in comm.received_messages:
                        print(f"Drone {drone.name} received message {msg}")

        self._messages = {}

        # Capture the frame
        self.recorder.capture_frame(self)

        self.fps_display.update(display=False)

        # print("can_grasp: {}, entities: {}".format(self._drone.base.grasper.can_grasp,
        #                                            self._drone.base.grasper.grasped_entities))

        if self._terminate:
            self.recorder.end_recording()
            self._last_image = self.get_playground_image()
            arcade.close_window()

    def get_playground_image(self):
        self.update()
        # The image should be flip and the color channel permuted
        image = cv2.flip(self.get_np_img(), 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def draw(self, force=False):
        arcade.start_render()
        self.update_sprites(force)

        self._playground.window.use()
        self._playground.window.clear(self._background)

        if self._draw_lidar:
            for drone in self._playground.agents:
                drone.lidar().draw()

        if self._draw_semantic:
            for drone in self._playground.agents:
                drone.semantic().draw()

        if self._draw_touch:
            for drone in self._playground.agents:
                drone.touch().draw()

        self._mouse_measure.draw(enable=self._use_mouse_measure)
        self._visu_noises.draw(enable=self._enable_visu_noises)

        self._transparent_sprites.draw(pixelated=True)
        self._interactive_sprites.draw(pixelated=True)
        self._zone_sprites.draw(pixelated=True)
        self._visible_sprites.draw(pixelated=True)
        self._traversable_sprites.draw(pixelated=True)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        self._keyboardController.on_key_press(key, modifiers)
        if self._drones:

            if key == arcade.key.M:
                self._messages = {
                    self._drones[0]: {
                        self._drones[0].communicator: (
                            None,
                            f"Currently at timestep {self._playground.timestep}",
                        )
                    }
                }
                print(f"Drone {self._drones[0].name} sends message")

        if key == arcade.key.Q:
            self._terminate = True

        if key == arcade.key.R:
            self._playground.reset()
            self._visu_noises.reset()

        if key == arcade.key.S:
            self._draw_semantic = not self._draw_semantic

        if key == arcade.key.T:
            self._draw_touch = not self._draw_touch

        if key == arcade.key.L:
            self._draw_lidar = not self._draw_lidar

    def on_key_release(self, key, modifiers):
        self._keyboardController.on_key_release(key, modifiers)

    # Creating function to check the position of the mouse
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self._mouse_measure.on_mouse_motion(x, y, dx, dy)

    # Creating function to check the mouse clicks
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self._mouse_measure.on_mouse_press(x, y, button, enable=self._use_mouse_measure)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self._mouse_measure.on_mouse_release(x, y, button, enable=self._use_mouse_measure)

    def collect_all_messages(self, drones: List[DroneAbstract]):
        messages: SentMessagesDict = {}
        for i in range(self._number_drones):
            msg_data = drones[i].define_message_for_all()
            messages[drones[i]] = {drones[i].communicator: (None, msg_data)}
        return messages

    @property
    def last_image(self):
        return self._last_image

    @property
    def elapsed_time(self):
        return self._elapsed_time

    @property
    def real_time_elapsed(self):
        return self._real_time_elapsed

    @property
    def rescued_number(self):
        return self._rescued_number

    @property
    def rescued_all_time_step(self):
        return self._rescued_all_time_step
