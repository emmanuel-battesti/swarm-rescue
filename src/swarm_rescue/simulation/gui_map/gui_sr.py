import math
import time
from typing import Optional, Tuple, List, Dict
import sys

import arcade
import cv2

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.controller import CommandName, Command
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.gui_map.keyboard_controller import KeyboardController
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.gui_map.playground import AllSentMessagesDict
from swarm_rescue.simulation.gui_map.status_bar import StatusBar
from swarm_rescue.simulation.gui_map.top_down_view import TopDownView
from swarm_rescue.simulation.gui_map.window_icon import apply_window_icon
from swarm_rescue.simulation.reporting.screen_recorder import ScreenRecorder
from swarm_rescue.simulation.utils.constants import (
    FRAME_RATE,
    DRONE_INITIAL_HEALTH,
    WINDOW_LETTERBOX_COLOR,
    MAX_WINDOW_WIDTH,
    MAX_WINDOW_HEIGHT,
)
from swarm_rescue.simulation.utils.fps_display import FpsDisplay
from swarm_rescue.simulation.utils.mouse_measure import MouseMeasure
from swarm_rescue.simulation.utils.visu_noises import VisuNoises


class GuiSR(TopDownView, arcade.View):
    """
    The GuiSR class is a subclass of TopDownView and arcade.View, providing a graphical user
    interface for the simulation. It handles the rendering of the playground,
    drones, and other visual elements, as well as user input and interaction.
    """

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
            draw_status_bar: bool = True,
            filename_video_capture: Optional[str] = None,
            headless: bool = False,
            window_scale: Optional[float] = None,
    ) -> None:
        """
        Initialize the GuiSR graphical user interface.

        Args:
            the_map (MapAbstract): The map object containing the playground and drones.
            size (Optional[Tuple[int, int]]): Size of the offscreen framebuffer
                (and of the recorded video), i.e. the resolution everything is
                computed at. Not the window size: see `window_scale`.
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
            draw_status_bar (bool): Draw the black band across the top of the
                window, carrying the map name on the left and the round
                progress on the right. The band is drawn in window coordinates
                by `on_draw()` only, so it never reaches the offscreen uid
                image the ray sensors read, nor the recorded video.
            filename_video_capture (str): Output filename for video capture.
            headless (bool): Run in headless mode without visible window.
            window_scale (Optional[float]): Window size relative to `size`.
                None (the default) opens the window as large as `size` allows
                while staying within `MAX_WINDOW_WIDTH` x `MAX_WINDOW_HEIGHT`
                (1366x768), preserving the map aspect ratio. An explicit value
                is applied first, then still capped to those bounds. This only
                scales the window: the map keeps being rendered at `size` and
                the whole map stays visible, the camera simply shows it in fewer
                pixels. The window remains resizable afterward.
        """
        # The map builds its playground in its own `__init__`, so by the time
        # a GUI is created for it there is one. The assertion documents that
        # for the type checker and fails loudly if the invariant breaks.
        playground = the_map.playground
        assert playground is not None, "The map has no playground to display yet."

        # Initialize size from provided value or playground/fallback
        if size is None:
            size = playground.size if playground.size else (1200, 800)

        TopDownView.__init__(
            self,
            playground=playground,
            size=size,
            center=center,
            zoom=zoom,
            use_color_uid=use_color_uid,
            draw_transparent=draw_transparent,
            draw_interactive=draw_interactive,
            draw_zone=draw_zone,
        )

        arcade.View.__init__(self, window=self._playground.window, background_color=self._background)

        self._headless = headless

        # The window is opened smaller than the offscreen framebuffer, so it does
        # not take the whole screen. `self._size` (the framebuffer, the recorded
        # video, and the resolution everything is computed at) is untouched: the
        # map is still rendered at full size and still entirely visible, the
        # camera just presents it in fewer pixels.
        self._window_size = self._scaled_window_size(size, window_scale)
        self._playground.window.set_size(*self._window_size)
        self._playground.window.set_visible(not self._headless)
        self._playground.window.headless = self._headless

        # Aspect ratio that must be preserved: the one of the map.
        # Defined before show_view(), which triggers on_show_view().
        self._aspect_ratio = self._size[0] / self._size[1] if self._size[1] > 0 else 1.0

        # `position=(0, 0)` is required, and not cosmetic.
        #
        # Left at its default, a `Camera2D` sits at `(half_width, half_height)`
        # -- the center of the screen -- because its projection is meant to run
        # from 0 to the window size, so (0, 0) lands in its bottom-left corner.
        # This view uses a *centered* projection (see below), so that default
        # shifts the whole map by half the window: on MapMedium01 (window
        # 830x561) the world origin landed on screen at (415, 280) instead of
        # (415, 280.5) once the letterbox is accounted for -- the map was
        # visibly drawn a whole half-window down and to the right of where it
        # belonged.
        self.camera = arcade.Camera2D(window=self._playground.window,
                                      position=(0, 0))
        width, height = self._size
        # Symmetric bounds, so the world origin is exactly at the center of the
        # image and the map is not shifted by half a pixel.
        #
        # The parentheses are not cosmetic. `-width // 2` is `(-width) // 2`, and
        # Python floors toward minus infinity, so for an odd width it returns
        # `-width // 2 - 1`: the projection then spans one pixel too much on the
        # left and its center sits at -0.5 instead of 0. Maps are not always
        # even-sized -- MapMedium02 is 1113x750 and MapFinal2022_23 is
        # 1819x1350 -- and both were visibly drawn half a pixel left and down.
        half_width = width // 2
        half_height = height // 2
        self.camera.projection = arcade.types.LRBT(
            -half_width, half_width, -half_height, half_height,
        )

        # The black band at the top of the window. Its map name is the class
        # name, the same identifier the launcher and the reports use
        # (`launcher.py` prints `type(the_map).__name__`), so what the window
        # says and what the console says cannot drift apart.
        #
        # Built before `show_view()` below, which triggers `on_show_view()` ->
        # `_update_camera_viewport()` -> `_reserved_top_height()`: the camera
        # has to know how much of the window the band takes on its very first
        # call, otherwise the first layout would letterbox the map as if the
        # band did not exist.
        #
        # None when `draw_status_bar` is off, which is how both `on_draw()` and
        # `_reserved_top_height()` know there is nothing to paint.
        self._status_bar = StatusBar(type(the_map).__name__) \
            if draw_status_bar else None

        # The drone icon in the title bar. Applied here rather than inside
        # `set_caption` so it happens once, with the rest of the window setup.
        # Best effort: a window that refuses an icon still runs.
        apply_window_icon(self._playground.window)

        self._playground.window.set_update_rate(FRAME_RATE)
        self._playground.window.show_view(self)

        self._the_map = the_map
        self._drones = self._the_map.drones
        self._number_drones = self._the_map.number_drones

        # Limits as the map declares them. None means "no limit": the checks
        # below skip the comparison instead of comparing against a sentinel, so
        # an unlimited round is exactly that, and the status bar can leave its
        # progress label out on its own.
        self._max_timestep_limit = self._the_map.max_timestep_limit
        self._max_walltime_limit = self._the_map.max_walltime_limit

        self._drones_commands: Optional[Dict[Agent, Dict[CommandName, Command]]] = None
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

        self._total_number_wounded_persons = self._the_map.number_wounded_persons
        self._reset_round_counters()

        self._last_image = None
        self._terminate = False
        self._force_exit = False
        self._has_crashed = False
        self._error_msg = ""
        # Set as soon as the window is closed, because pyglet keeps calling
        # on_update/on_draw for a frame or two afterward while the GL context is
        # already gone: any further GL call raises
        # `GLException: No GL context; create a Window first`.
        self._window_closed = False

        self.fps_display = FpsDisplay(period_display=2)
        self._keyboardController = KeyboardController()
        self._mouse_measure = MouseMeasure(screen_to_world=self.screen_to_world)
        assert playground.size is not None
        self._visu_noises = VisuNoises(playground_size=playground.size,
                                       drones=self._drones)

        # Initialize the video recorder. The framebuffer keeps the map size for
        # the whole run, so the recorded resolution is stable and unaffected by
        # the user resizing the window.
        self.recorder = ScreenRecorder(self._size[0], self._size[1], fps=30,
                                       out_file=filename_video_capture)

        # The view is drawn at the map size, so the zoom only has to be set once.
        self._fit_map_to_window()
        self.update_sprites_position(force=True)

    @staticmethod
    def _scaled_window_size(size: Tuple[int, int],
                            window_scale: Optional[float]) -> Tuple[int, int]:
        """
        Compute the initial window size from the framebuffer size.

        The window is only a presentation surface: the map is rendered offscreen
        at `size` and the camera projection keeps showing the same world area, so
        scaling the window down keeps the whole map visible in fewer pixels.

        With `window_scale` None, the window opens at the largest size that fits
        in `MAX_WINDOW_WIDTH` x `MAX_WINDOW_HEIGHT` (1366x768), instead of a
        fixed fraction of the map size that could be far too large or too small
        depending on the map.

        The result is always capped to `MAX_WINDOW_WIDTH` x `MAX_WINDOW_HEIGHT`
        while preserving the aspect ratio, so the window never opens larger than
        the target screen even when an explicit `window_scale` asks for more.
        Resizing afterward is unaffected: this only sets the initial size.

        A window of 0 or 1 pixel cannot be used, and arcade requires positive
        integers, so the result is clamped to at least 2x2. A non-positive or
        non-finite `window_scale` is ignored rather than raised: a window size is
        not worth refusing to start over.
        """
        if window_scale is None or not math.isfinite(window_scale) or window_scale <= 0:
            scale = 1.0
        else:
            scale = window_scale
        width = int(size[0] * scale)
        height = int(size[1] * scale)

        cap_scale = min(1.0,
                        MAX_WINDOW_WIDTH / width if width > 0 else 1.0,
                        MAX_WINDOW_HEIGHT / height if height > 0 else 1.0)
        width = int(width * cap_scale)
        height = int(height * cap_scale)
        return max(2, width), max(2, height)

    def screen_to_world(self, pt_pix: tuple[float | int, float | int]) -> tuple[float, float]:
        v = self.camera.unproject(pt_pix)
        return v.x, v.y

    def close(self) -> None:
        """
        Close the simulation window.
        """
        self._playground.close_window()

    def _reset_round_counters(self) -> None:
        """
        Bring the round counters back to their values at the start of a round.

        These are the numbers the status bar shows -- elapsed steps, wall time,
        rescued wounded -- plus the flag that records the walltime limit. They
        live in the view rather than in the playground, so `Playground.reset()`
        cannot restore them: without this, a reset round would keep the previous
        round's counters, and the bar would show the end of the round it just
        restarted.
        """
        self._rescued_number = 0
        self._full_rescue_timestep = 0
        self._elapsed_timestep = 0
        self._start_timestamp = time.time()
        self._is_max_walltime_limit_reached = False
        self._elapsed_walltime = 0.001

    def _status_bar_wounded_total(self) -> Optional[int]:
        """
        Number of wounded persons to report in the status bar, or None.

        The rescue counter only makes sense on a map that has somewhere to
        bring the wounded and somebody to bring: it is left out when the
        playground holds no rescue center, and when the map declares no wounded
        person (or a count of zero).

        Returns:
            Optional[int]: The total to display, None when the counter must
            be hidden.
        """
        if not self._total_number_wounded_persons:
            return None

        if not any(isinstance(element, RescueCenter)
                   for element in self._playground.elements):
            return None

        return int(self._total_number_wounded_persons)

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
        self._playground.window.show_view(self)
        self._playground.window.run()

    def on_show_view(self) -> None:
        super().on_show_view()
        # The window may have been resized while the view was hidden.
        self._update_camera_viewport(self.window.width, self.window.height)

    def on_draw(self) -> None:
        """
        Render the current frame to the window.
        """
        # Nothing can be drawn once the window is closed: the GL context is gone
        # and every draw call would raise. pyglet still schedules a few frames
        # after `close()`, so this guard is what keeps the shutdown silent.
        if self._window_closed:
            return

        # The whole window is cleared with the letterbox color, then only the
        # map area (the aspect ratio constrained viewport) is cleared with the
        # playground background color. The map is then drawn by draw() inside
        # that viewport, leaving the letterbox color visible around it.
        self.clear(color=WINDOW_LETTERBOX_COLOR)
        self.clear(color=self._background, viewport=self.camera.viewport.lbwh_int)
        self.draw()

        # The status bar goes last, and only here.
        #
        # `on_draw()` is the window frame callback, and the bar is the only
        # thing drawn outside the camera: it activates its own projection over
        # the whole window, so its coordinates are window pixels rather than
        # map pixels. Keeping it here is what keeps it away from the sensors --
        # the lidars read the offscreen uid image, produced by
        # `update_and_draw_in_framebuffer()`, which never sees this frame.
        if self._status_bar is not None:
            self._status_bar.draw(
                window=self._playground.window,
                elapsed_timestep=self._elapsed_timestep,
                max_timestep_limit=self._max_timestep_limit,
                elapsed_walltime=self._elapsed_walltime,
                max_walltime_limit=self._max_walltime_limit,
                rescued_number=self._rescued_number,
                total_wounded_persons=self._status_bar_wounded_total(),
            )

    def on_update(self, delta_time: float) -> None:
        """
        Update the simulation state and draw the playground and entities.

        Args:
            delta_time (float): Time since last update.
        """
        try:
            # The simulation is over and the window has been closed: the GL
            # context is gone, so stepping (which re-renders the uid
            # image) would raise. pyglet can still call this a few more times.
            if self._window_closed:
                return

            self._elapsed_timestep += 1

            if self._elapsed_timestep < 2:
                self._playground.step(all_commands=self._drones_commands,
                                      all_messages=self._messages)
                # self._the_map.explored_map.update(self._drones)
                # self._the_map.explored_map._process_positions()
                # self._the_map.explored_map.display()
                self.update_sprites_position(force=True)
                return


            self._the_map.explored_map.update_drones(self._drones)
            # self._the_map.explored_map._process_positions()
            # self._the_map.explored_map.display()

            # COMPUTE ALL THE MESSAGES
            self._messages = self.collect_all_messages(self._drones)

            # COMPUTE COMMANDS
            for i in range(self._number_drones):
                if self._drones[i].removed or self._drones[i].is_dead:
                    # Drone was destroyed (e.g. too much collision): its
                    # sensors are not updated, so control() would run
                    # on stale/frozen data. Skip it entirely.
                    self._drones_commands[self._drones[i]] = {}
                    continue

                self._drones[i].elapsed_walltime = self._elapsed_walltime
                self._drones[i].elapsed_timestep = self._elapsed_timestep
                # The ground-truth accessors (true_position, true_angle) are
                # refused while the participant's code runs, see
                # DroneAbstract.participant_code.
                with self._drones[i].participant_code():
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
            # A missing limit means the round is not bound by that criterion.
            if (self._max_walltime_limit is not None
                    and self._elapsed_walltime > self._max_walltime_limit):
                self._elapsed_walltime = self._max_walltime_limit
                self._is_max_walltime_limit_reached = True
                self._terminate = True

            if (self._max_timestep_limit is not None
                    and self._elapsed_timestep > self._max_timestep_limit):
                self._elapsed_timestep = self._max_timestep_limit
                self._terminate = True

            if self._print_rewards:
                for agent in self._playground.agents:
                    if agent.reward != 0:
                        print(agent.reward)

            if self._print_messages:
                for drone in self._playground.agents:
                    for comm in drone.communicators:
                        for sender, msg in comm.received_messages:
                            print(f"{drone.name} <- {sender.agent.name}: {msg}")

            self._messages = {}

            # Capture the frame
            # Au bon endroit ? Il faudrait le mettre avant le draw() ?
            self.recorder.capture_frame(self)

            self.fps_display.update(display=False)

            # print("can_grasp: {}, entities: {}".format(self._drone.grasper.can_grasp,
            #                                            self._drone.grasper.grasped_wounded_persons))

        except Exception:
            # Log the exception and force termination
            import traceback
            self._has_crashed = True
            self._error_msg = ("\n" + "="*70 + "\n"
                               + "EXCEPTION in on_update():\n"
                               + "="*70 + "\n"
                               + traceback.format_exc()
                               + "="*70)
            print(self._error_msg)
            self._terminate = True

        finally:
            if self._terminate and not self._window_closed:
                # Order matters: the last image is read from the offscreen
                # framebuffer, which needs the GL context, and only then is the
                # window closed.
                self._window_closed = True
                self.compute_health_stats()
                self.recorder.end_recording()
                self._last_image = self.get_playground_image()
                self._playground.window.close()
                if self._force_exit:
                    sys.exit(0)

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
        self.update_sprites_position(force)

        with self.camera.activate():
            for drone in self._drones:
                drone.draw_bottom_layer()

            if self._draw_lidar_rays:
                for drone in self._drones:
                    drone.lidar().draw()

            if self._draw_semantic_rays:
                for drone in self._drones:
                    drone.semantic().draw()

            if self._draw_gps:
                for drone in self._drones:
                    drone.draw_gps()

            if self._draw_com:
                for drone in self._drones:
                    drone.draw_com()

            self._mouse_measure.draw(enable=self._use_mouse_measure)
            self._visu_noises.draw(enable=self._enable_visu_noises)

            if self._draw_transparent:
                self._transparent_sprites.draw()

            if self._draw_interactive:
                self._interactive_sprites.draw()

            if self._draw_zone:
                self._zone_sprites.draw()

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

            self._visible_sprites.draw()

            for drone in self._drones:
                drone.draw_top_layer()

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
            self._terminate = True
            self._force_exit = True

        if key == arcade.key.R:
            # Resetting re-registers the entities and touches the GPU, so it is
            # refused once the window is closed, like any other GL operation.
            if not self._window_closed:
                self._playground.reset()
                self._visu_noises.reset()
                # The playground restores the scene, not the round counters
                # kept by the view: reset both, or the bar keeps showing the
                # end of the round that was just restarted.
                self._reset_round_counters()

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
            # Same guard as for control(): the message a participant sends to
            # the swarm must be built from the simulated sensors too.
            with drones[i].participant_code():
                msg_data = drones[i].define_message_for_all()
            messages[drones[i]] = {drones[i].communicator: (None, msg_data)}
        return messages

    def compute_health_stats(self) -> None:
        """
        Compute statistics about drone health and destruction.
        """
        sum_health = 0
        nb_destroyed = 0
        for drone in self._drones:
            sum_health += drone.drone_health
            if drone.drone_health <= 0:
                nb_destroyed += 1

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

    @property
    def has_crashed(self) -> bool:
        """
        Returns whether the simulation crashed during the round.

        Returns:
            bool: True if crashed, False otherwise.
        """
        return self._has_crashed

    @property
    def error_msg(self) -> str:
        """
        Returns the error message if the simulation crashed.

        Returns:
            str: Error message / traceback.
        """
        return self._error_msg

    def on_resize(self, width: int, height: int) -> None:
        """
        Called when the user resizes the window.

        Nothing is forced here: the window keeps the size the user asked for.
        We only ask the camera to constrain its viewport to the map aspect
        ratio, which letterboxes the map inside the window (see
        `_update_camera_viewport`).
        """
        self._update_camera_viewport(width, height)

    def _update_camera_viewport(self, width: int, height: int) -> None:
        """
        Resize the camera viewport to (width, height) while preserving the
        aspect ratio of the map.

        The map area is what remains of the window *below the status bar*, and
        the viewport is centered in that area, so the leftover space is split
        evenly between the opposite sides. The rest of the window is left
        untouched and shows the letterbox color (see `on_draw`).

        Centering is not something this method has to compute: `XYWH` is
        center-based, and `update_values` re-centers the aspect-constrained
        rectangle on the center it was handed. So the whole reservation is
        "give me a rectangle centered on the area under the band".

        That the bar overlaps nothing is the whole point of carving the
        rectangle out this way. Drawn over the top of a full-height viewport,
        the band would cover the upper rows of the map -- which is the one
        thing a status bar must never do, since those rows are map content
        (and, in a windowed run, the part a participant is watching).
        """
        if width <= 0 or height <= 0:
            return

        # Never let the map area collapse: a window shorter than the band would
        # otherwise leave a negative height, and `update_values` would build a
        # zero-sized viewport -- which divides by zero in `unproject`, so the
        # mouse tool would raise. One pixel of map is worse than none.
        map_area_height = max(1, height - self._reserved_top_height(height))

        self.camera.update_values(
            # Center-based: this is the full area below the band, and
            # `update_values` shrinks it to the map aspect around this center.
            arcade.types.XYWH(width / 2.0, map_area_height / 2.0,
                              width, map_area_height),
            aspect=self._aspect_ratio,
            projection=False,
        )

        # The scissor clips the drawing to the map area, so the letterbox color is
        # preserved outside it.
        self.camera.scissor = self.camera.viewport

    def _reserved_top_height(self, window_height: int) -> int:
        """
        How many pixels at the top of the window the status bar takes.

        Delegates to `StatusBar.effective_height`, the same number `draw()`
        paints the band with. Sharing it is the point: the reservation and the
        band cannot drift apart, so the band cannot end up covering map rows
        because one side used a different clamp than the other.

        Args:
            window_height (int): Height of the window, in pixels.

        Returns:
            int: Reserved height in pixels, 0 when there is no bar.
        """
        if self._status_bar is None:
            return 0

        return self._status_bar.effective_height(window_height)

    def _fit_map_to_window(self) -> None:
        """
        Compute the zoom so the whole playground fits in the view, and center
        the view on the map.

        The view is rendered at the map size and the camera projection is
        fixed, so this only needs to be done once at initialization.
        """
        world_size = self._playground.size
        if not world_size or world_size[0] <= 0 or world_size[1] <= 0:
            return

        map_w, map_h = world_size
        self.set_zoom(min(self._size[0] / map_w, self._size[1] / map_h))
        self.set_center((0, 0))
        self.update_sprites_position(force=True)
