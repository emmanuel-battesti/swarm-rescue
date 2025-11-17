import time
from typing import Optional, Tuple, List, Dict
import sys
import time

import arcade
import cv2

from swarm_rescue.simulation.drone.controller import CommandName, Command
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.keyboard_controller import KeyboardController
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.gui_map.playground import AllSentMessagesDict
from swarm_rescue.simulation.gui_map.top_down_view import TopDownView
from swarm_rescue.simulation.reporting.screen_recorder import ScreenRecorder
from swarm_rescue.simulation.utils.constants import FRAME_RATE, DRONE_INITIAL_HEALTH, ENABLE_WINDOW_AUTO_RESIZE
from swarm_rescue.simulation.utils.fps_display import FpsDisplay
from swarm_rescue.simulation.utils.mouse_measure import MouseMeasure
from swarm_rescue.simulation.utils.visu_noises import VisuNoises
from swarm_rescue.simulation.utils.window_utils import auto_resize_window


class GuiSR(TopDownView):
    """
    The GuiSR class is a subclass of TopDownView and provides a graphical user
    interface for the simulation. It handles the rendering of the playground,
    drones, and other visual elements, as well as user input and interaction.
    """


    def _handle_window_auto_resize(self, the_map: MapAbstract, size: Optional[Tuple[int, int]],
                                  zoom: float, headless: bool) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Handle automatic window resizing for small screens.

        Args:
            the_map: The map object containing the playground
            size: Initial window size
            zoom: Initial zoom factor
            headless: Whether running in headless mode

        Returns:
            Tuple of (adjusted_size, adjusted_zoom)
        """
        # Auto-resize window if needed for small screens (before window creation)
        if not headless and ENABLE_WINDOW_AUTO_RESIZE:
            # If size is None, use the playground size or a default
            if size is None:
                size = the_map.playground.size if the_map.playground.size else (1200, 800)

            # Check if this is a problematic map size that causes rendering issues
            problematic_sizes = [(1660, 1122)]  # MapMedium01 and similar
            is_problematic = size in problematic_sizes

            if not is_problematic:
                # Apply auto-resize with zoom adjustment only for non-problematic maps
                adjusted_size, calculated_zoom = auto_resize_window(size)
                if adjusted_size != size:
                    size = adjusted_size
                    zoom = zoom * calculated_zoom # Apply the calculated zoom factor
            else:
                # For problematic maps, disable auto-resize completely
                # Let the user handle window size manually or use system defaults
                print(f"Auto-resize désactivé pour cette carte ({size[0]}x{size[1]})")
        elif not headless and not ENABLE_WINDOW_AUTO_RESIZE:
            # Auto-resize is globally disabled
            if size is None:
                size = the_map.playground.size if the_map.playground.size else (1200, 800)
            print("Auto-resize désactivé globalement via ENABLE_WINDOW_AUTO_RESIZE")

        return size, zoom

    def __init__(
            self,
            the_map: MapAbstract,
            size: Optional[Tuple[int, int]] = None,
            center: Tuple[float, float] = (0, 0),
            zoom: float = 1,
            use_keyboard: bool = False,
            use_color_uid: bool = False,
            draw_transparent: bool = False,
            draw_interactive: bool = False,
            draw_zone: bool = True,
            draw_lidar_rays: bool = False,
            draw_semantic_rays: bool = False,
            draw_gps: bool = False,
            draw_com: bool = False,
            print_rewards: bool = False,
            print_messages: bool = False,
            use_mouse_measure: bool = False,
            enable_visu_noises: bool = False,
            filename_video_capture: str = None,
            headless: bool = False,
    ) -> None:
        """
        Initialize the GuiSR graphical user interface.

        Args:
            the_map (MapAbstract): The map object containing the playground and drones.
            size (Optional[Tuple[int, int]]): Size of the window.
            center (Tuple[float, float]): Center of the view.
            zoom (float): Zoom factor.
            use_keyboard (bool): Enable keyboard control for the first drone.
            use_color_uid (bool): Use color UID for sprites.
            draw_transparent (bool): Draw transparent sprites.
            draw_interactive (bool): Draw interactive sprites.
            draw_zone (bool): Draw zone sprites.
            draw_lidar_rays (bool): Draw lidar sensor rays.
            draw_semantic_rays (bool): Draw semantic sensor rays.
            draw_gps (bool): Draw GPS sensor visualization.
            draw_com (bool): Draw communication visualization.
            print_rewards (bool): Print rewards to console.
            print_messages (bool): Print messages to console.
            use_mouse_measure (bool): Enable mouse measurement tool.
            enable_visu_noises (bool): Enable visualization of sensor noises.
            filename_video_capture (str): Output filename for video capture.
        """
        # Handle automatic window resizing
        size, zoom = self._handle_window_auto_resize(the_map, size, zoom, headless)

        super().__init__(
            the_map.playground,
            size,
            center,
            zoom,
            use_color_uid,
            draw_transparent,
            draw_interactive,
            draw_zone,
        )


        self._headless = headless
        self._playground.window.set_size(*self._size)


        # image_icon = pyglet.resource.image("resources/drone_v2.png")
        # self._playground.window.set_icon(image_icon)
        # Ok for the first round, crash for the second round ! I dont know
        # why...

        self._playground.window.set_visible(not self._headless)
        self._playground.window.headless = self._headless

        self._playground.window.on_draw = self.on_draw
        self._playground.window.on_update = self.on_update
        self._playground.window.on_key_press = self.on_key_press
        self._playground.window.on_key_release = self.on_key_release
        self._playground.window.on_mouse_motion = self.on_mouse_motion
        self._playground.window.on_mouse_press = self.on_mouse_press
        self._playground.window.on_mouse_release = self.on_mouse_release
        self._playground.window.set_update_rate(FRAME_RATE)
        # self._playground.window.set_location(4500, 0)

        self._the_map = the_map
        self._drones = self._the_map.drones
        self._number_drones = self._the_map.number_drones

        self._max_walltime_limit = self._the_map.max_walltime_limit
        if self._max_walltime_limit is None:
            self._max_walltime_limit = 100000000

        self._max_timestep_limit = self._the_map.max_timestep_limit
        if self._max_timestep_limit is None:
            self._max_timestep_limit = 100000000

        self._drones_commands: Optional[Dict[DroneAbstract, Dict[CommandName, Command]]] = None
        if self._drones:
            self._drones_commands = {}

        self._messages = None
        self._print_rewards = print_rewards
        self._print_messages = print_messages

        self._use_keyboard = use_keyboard

        self._draw_lidar_rays = draw_lidar_rays
        self._draw_semantic_rays = draw_semantic_rays
        self._draw_gps = draw_gps
        self._draw_com = draw_com
        self._use_mouse_measure = use_mouse_measure
        self._enable_visu_noises = enable_visu_noises

        # 'number_wounded_persons' is the number of wounded persons that should
        # be retrieved by the drones.
        self._percent_drones_destroyed = 0.0
        self._mean_drones_health = 0.0

        self._total_number_wounded_persons = (
            self._the_map.number_wounded_persons)
        self._rescued_number = 0
        self._full_rescue_timestep = 0
        self._elapsed_timestep = 0
        self._start_timestamp = time.time()
        self._is_max_walltime_limit_reached = False
        self._elapsed_walltime = 0.001

        self._last_image = None
        self._terminate = False

        self.fps_display = FpsDisplay(period_display=2)
        self._keyboardController = KeyboardController()
        self._mouse_measure = MouseMeasure(playground_size=the_map.playground.size)
        self._visu_noises = VisuNoises(playground_size=the_map.playground.size,
                                       drones=self._drones)

        self.recorder = ScreenRecorder(self._size[0], self._size[1], fps=30,
                                       out_file=filename_video_capture)

    def close(self) -> None:
        """
        Close the simulation window.
        """
        self._playground.close_window()

    def set_caption(self, window_title: str) -> None:
        """
        Set the window caption/title.

        Args:
            window_title (str): The title to set.
        """
        self._playground.window.set_caption(window_title)

    def run(self) -> None:
        """
        Start the simulation event loop.
        """
        self._playground.window.run()


    def on_draw(self) -> None:
        """
        Render the current frame to the window.
        """
        # Clear the window
        self._playground.window.clear()
        # Binding the framebuffer object to the window
        # Is it necessary ? It seems to work without it.
        self._fbo.use()

        # Draw the playground and all the entities in it
        # Copier le contenu de draw() ici ?
        self.draw()

    def on_update(self, delta_time: float) -> None:
        """
        Update the simulation state and draw the playground and entities.

        Args:
            delta_time (float): Time since last update.
        """
        self._elapsed_timestep += 1

        if self._elapsed_timestep < 2:
            self._playground.step(all_commands=self._drones_commands,
                                  all_messages=self._messages)
            # self._the_map.explored_map.update(self._drones)
            # self._the_map.explored_map._process_positions()
            # self._the_map.explored_map.display()
            return

        self._the_map.explored_map.update_drones(self._drones)
        # self._the_map.explored_map._process_positions()
        # self._the_map.explored_map.display()

        # COMPUTE ALL THE MESSAGES
        self._messages = self.collect_all_messages(self._drones)

        # COMPUTE COMMANDS
        for i in range(self._number_drones):
            self._drones[i].elapsed_walltime = self._elapsed_walltime
            self._drones[i].elapsed_timestep = self._elapsed_timestep
            command = self._drones[i].control()
            if self._use_keyboard and i == 0:
                command = self._keyboardController.control()

            self._drones_commands[self._drones[i]] = command

        if self._drones:
            self._drones[0].display()

        self._playground.step(all_commands=self._drones_commands,
                              all_messages=self._messages)

        # self._playground.debug_draw()

        self._visu_noises.update(enable=self._enable_visu_noises)
        # self._the_map.explored_map.display()

        # REWARDS
        new_reward = 0
        for i in range(self._number_drones):
            new_reward += self._drones[i].reward

        if new_reward != 0:
            self._rescued_number += new_reward

        if (self._rescued_number == self._total_number_wounded_persons
                and self._full_rescue_timestep == 0):
            self._full_rescue_timestep = self._elapsed_timestep

        last_timestamp = time.time()
        # last_elapsed_walltime = self._elapsed_walltime
        self._elapsed_walltime = (last_timestamp - self._start_timestamp)
        # delta = self._elapsed_walltime - last_elapsed_walltime
        # if delta > 0.5:
        #     print("self._elapsed_walltime = {:.1f}, delta={:.1f},
        #     freq={:.1f}, freq moy={:.1f}".format(
        #         self._elapsed_walltime,
        #         delta,
        #         1 / (delta + 0.0001),
        #         self._elapsed_timestep / (self._elapsed_walltime + 0.00001)))
        if self._elapsed_walltime > self._max_walltime_limit:
            self._elapsed_walltime = self._max_walltime_limit
            self._is_max_walltime_limit_reached = True
            self._terminate = True

        if self._elapsed_timestep > self._max_timestep_limit:
            self._elapsed_timestep = self._max_timestep_limit
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
        # Au bon endroit ? Il faudrait le mettre avant le draw() ?
        self.recorder.capture_frame(self)

        self.fps_display.update(display=False)

        # print("can_grasp: {}, entities: {}".format(self._drone.grasper.can_grasp,
        #                                            self._drone.grasper.grasped_wounded_persons))

        if self._terminate:
            self.compute_health_stats()
            self.recorder.end_recording()
            self._last_image = self.get_playground_image()
            arcade.close_window()

    def get_playground_image(self) -> cv2.typing.MatLike:
        """
        Get the image of the playground in the framebuffer.

        Returns:
            Any: The image as a numpy array.
        """
        self.update_and_draw_in_framebuffer()
        # The image should be flip and the color channel permuted
        image = cv2.flip(self.get_np_img(), 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def draw(self, force: bool = False) -> None:
        """
        Draw the playground and all the entities in it in the window.

        Args:
            force (bool): If True, force update of all sprites.
        """
        arcade.start_render()
        self.update_sprites_position(force)

        self._playground.window.use()
        self._playground.window.clear(self._background)

        for drone in self._playground.agents:
            drone.draw_bottom_layer()

        if self._draw_lidar_rays:
            for drone in self._playground.agents:
                drone.lidar().draw()

        if self._draw_semantic_rays:
            for drone in self._playground.agents:
                drone.semantic().draw()

        if self._draw_gps:
            for drone in self._playground.agents:
                drone.draw_gps()

        if self._draw_com:
            for drone in self._playground.agents:
                drone.draw_com()

        self._mouse_measure.draw(enable=self._use_mouse_measure)
        self._visu_noises.draw(enable=self._enable_visu_noises)

        if self._draw_transparent:
            self._transparent_sprites.draw(pixelated=True)

        if self._draw_interactive:
            self._interactive_sprites.draw(pixelated=True)

        if self._draw_zone:
            self._zone_sprites.draw(pixelated=True)

        self._visible_sprites.draw(pixelated=True)

        for drone in self._playground.agents:
            drone.draw_top_layer()

        # display a circle representing semantic detection radius
        # width, height = self._size
        # drone = self._playground.agents[0]
        # x, y = drone.true_position()
        # x = x + width / 2
        # y = y + height / 2
        #
        # r = drone.true_angle()
        # for i in range(34):
        #     arcade.draw_line(x, y, x + 200 * cos(r + i * (2 * pi / 34)),
        #     y + 200 * sin(r + i * (2 * pi / 34)), (60, 120, 80))
        # # endregion

    def on_key_press(self, key: int, modifiers: int) -> None:
        """
        Called whenever a key is pressed.

        Args:
            key (int): The key code pressed.
            modifiers (int): Modifier keys pressed.
        """
        self._keyboardController.on_key_press(key, modifiers)

        if key == arcade.key.C:
            self._draw_com = not self._draw_com

        if key == arcade.key.P:
            self._draw_gps = not self._draw_gps

        if key == arcade.key.L:
            self._draw_lidar_rays = not self._draw_lidar_rays

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

        if key == arcade.key.E:
            print("Touche E pressée - Arrêt complet du programme...")
            arcade.close_window()
            sys.exit(0)

        if key == arcade.key.R:
            self._playground.reset()
            self._visu_noises.reset()

        if key == arcade.key.S:
            self._draw_semantic_rays = not self._draw_semantic_rays

    def on_key_release(self, key: int, modifiers: int) -> None:
        """
        Called whenever a key is released.

        Args:
            key (int): The key code released.
            modifiers (int): Modifier keys pressed.
        """
        self._keyboardController.on_key_release(key, modifiers)

    # Creating function to check the position of the mouse
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """
        Called whenever the mouse is moved.

        Args:
            x (int): X position.
            y (int): Y position.
            dx (int): Change in X.
            dy (int): Change in Y.
        """
        self._mouse_measure.on_mouse_motion(x, y, dx, dy)

    # Creating function to check the mouse clicks
    def on_mouse_press(self, x: int, y: int, button: int, _: int) -> None:
        """
        Called whenever a mouse button is pressed.

        Args:
            x (int): X position.
            y (int): Y position.
            button (int): Mouse button.
            _ (int): Modifier keys pressed.
        """
        self._mouse_measure.on_mouse_press(x, y, button,
                                           enable=self._use_mouse_measure)

    def on_mouse_release(self, x: int, y: int, button: int, _: int) -> None:
        """
        Called whenever a mouse button is released.

        Args:
            x (int): X position.
            y (int): Y position.
            button (int): Mouse button.
            _ (int): Modifier keys pressed.
        """
        self._mouse_measure.on_mouse_release(x, y, button,
                                             enable=self._use_mouse_measure)

    def collect_all_messages(self, drones: List[DroneAbstract]) -> AllSentMessagesDict:
        """
        Collect messages from all drones.

        Args:
            drones (List[DroneAbstract]): List of drones.

        Returns:
            AllSentMessagesDict: Dictionary of messages for each drone.
        """
        messages: AllSentMessagesDict = {}
        for i in range(self._number_drones):
            msg_data = drones[i].define_message_for_all()
            messages[drones[i]] = {drones[i].communicator: (None, msg_data)}
        return messages

    def compute_health_stats(self) -> None:
        """
        Compute statistics about drone health and destruction.
        """
        sum_health = 0
        for drone in self._playground.agents:
            sum_health += drone.drone_health

        nb_destroyed = self._number_drones - len(self._playground.agents)

        if self._number_drones > 0:
            self._mean_drones_health = sum_health / self._number_drones
            self._percent_drones_destroyed = nb_destroyed / self._number_drones * 100
        else:
            self._mean_drones_health = DRONE_INITIAL_HEALTH
            self._percent_drones_destroyed = 0.0

    @property
    def last_image(self):
        """
        Returns the last captured image of the playground.

        Returns:
            Any: The last image.
        """
        return self._last_image

    @property
    def percent_drones_destroyed(self) -> float:
        """
        Returns the percentage of drones destroyed.

        Returns:
            float: Percentage of destroyed drones.
        """
        return self._percent_drones_destroyed

    @property
    def mean_drones_health(self) -> float:
        """
        Returns the mean health of all drones.

        Returns:
            float: Mean drone health.
        """
        return self._mean_drones_health

    @property
    def elapsed_timestep(self) -> int:
        """
        Returns the number of elapsed timesteps.

        Returns:
            int: Elapsed timesteps.
        """
        return self._elapsed_timestep

    @property
    def elapsed_walltime(self) -> float:
        """
        Returns the elapsed wall time in seconds.

        Returns:
            float: Elapsed wall time.
        """
        return self._elapsed_walltime

    @property
    def rescued_number(self) -> int:
        """
        Returns the number of rescued wounded persons.

        Returns:
            int: Number rescued.
        """
        return self._rescued_number

    @property
    def full_rescue_timestep(self) -> int:
        """
        Returns the timestep at which all wounded persons were rescued.

        Returns:
            int: Full rescue timestep.
        """
        return self._full_rescue_timestep

    @property
    def is_max_walltime_limit_reached(self) -> bool:
        """
        Returns whether the maximum walltime limit has been reached.

        Returns:
            bool: True if reached, False otherwise.
        """
        return self._is_max_walltime_limit_reached
