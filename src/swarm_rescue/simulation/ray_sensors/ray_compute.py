from __future__ import annotations

from array import array
from os import path
from typing import TYPE_CHECKING, List

import numpy as np

from swarm_rescue.simulation.gui_map.top_down_view import TopDownView
from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import Playground


class RayCompute:
    """
    Class for computing ray-based ray_sensors hitpoints using shaders or CPU.
    """

    def __init__(self, playground: Playground, size, center, zoom, use_shader: bool = True):
        """
        Initialize RayCompute.

        Args:
            playground (Playground): The playground environment.
            size: Size of the view.
            center: Center of the view.
            zoom: Zoom factor.
            use_shader (bool): Whether to use shaders for computation.
        """
        self._ctx = playground.window._ctx

        self._use_shader = use_shader

        self._id_view = TopDownView(
            playground,
            size,
            center,
            zoom,
            use_color_uid=True,
            draw_interactive=False,
            draw_transparent=False,
            draw_zone=False,
        )

        self._sensors: List[RaySensor] = []

        if self._use_shader:
            self._view_params_buffer = self._ctx.buffer(
                data=array(
                    "f",
                    [
                        self._id_view.center[0],
                        self._id_view.center[1],
                        self._id_view.width,
                        self._id_view.height,
                        self._id_view.zoom,
                    ],
                )
            )

            self._view_params_buffer.bind_to_storage_buffer(binding=6)

            self._position_buffer = None
            self._param_buffer = None
            self._output_rays_buffer = None
            self._inv_buffer = None

            shader_dir = path.abspath(path.join(path.dirname(__file__), "shaders"))

            with open(path.join(shader_dir, "id_compute.glsl"), "rt", encoding="utf-8") as f_id:
                self._source_compute_ids = f_id.read()

            self._id_shader = None

    @property
    def _n_sensors(self) -> int:
        """
        Returns the number of sensors.
        """
        return len(self._sensors)

    @property
    def _max_n_rays(self) -> int:
        """
        Returns the maximum number of rays among all sensors.
        """
        return max(sensor.resolution for sensor in self._sensors)

    @property
    def _max_invisible(self) -> int:
        """
        Returns the maximum number of invisible elements among all sensors plus one.
        """
        return 1 + max(len(sensor.invisible_ids) for sensor in self._sensors)

    def _generate_buffers(self):
        """
        Generate GPU buffers for sensor computation.

        Returns:
            Tuple of buffers.
        """
        position_buffer = self._ctx.buffer(
            data=array("f", self._generate_position_buffer())
        )
        param_buffer = self._ctx.buffer(
            data=array("f", self._generate_parameter_buffer())
        )
        output_rays_buffer = self._ctx.buffer(
            data=array("f", self._generate_output_buffer())
        )
        inv_buffer = self._ctx.buffer(data=array("I", self._generate_invisible_buffer()))

        param_buffer.bind_to_storage_buffer(binding=2)
        position_buffer.bind_to_storage_buffer(binding=3)
        output_rays_buffer.bind_to_storage_buffer(binding=4)
        inv_buffer.bind_to_storage_buffer(binding=5)

        return position_buffer, param_buffer, output_rays_buffer, inv_buffer

    def _generate_parameter_buffer(self):
        """
        Generate parameter buffer for all sensors.
        """
        for sensor in self._sensors:
            yield sensor.max_range
            yield sensor.fov
            yield sensor.resolution
            yield sensor.n_points

    def _generate_position_buffer(self):
        """
        Generate position buffer for all sensors.
        """
        for sensor in self._sensors:
            yield sensor.position[0]
            yield sensor.position[1]
            yield sensor.angle

    def _generate_output_buffer(self):
        """
        Generate output buffer for all sensors.
        """
        for _ in range(self._n_sensors):
            for _ in range(self._max_n_rays):
                # View Position
                yield 0.0
                yield 0.0

                # Abs Env Position
                yield 0.0
                yield 0.0

                # Rel Position
                yield 0.0
                yield 0.0

                # Sensor center on view
                yield 0.0
                yield 0.0

                # ID
                yield 0.0

                # Distance
                yield 0.0

    def _generate_invisible_buffer(self):
        """
        Generate buffer for invisible elements for all sensors.
        """
        for sensor in self._sensors:

            count = 1
            yield sensor.anchor.uid

            for inv in sensor.invisible_ids:
                yield inv
                count += 1

            while count < self._max_invisible:
                yield 0
                count += 1

    def _generate_shaders(self):
        """
        Generate compute shaders for sensor computation.
        """
        new_source = self._source_compute_ids
        new_source = new_source.replace("N_SENSORS", str(len(self._sensors)))
        new_source = new_source.replace("MAX_N_RAYS", str(self._max_n_rays))
        new_source = new_source.replace("MAX_N_INVISIBLE", str(self._max_invisible))
        id_shader = self._ctx.compute_shader(source=new_source)

        return id_shader

    def add(self, sensor) -> None:
        """
        Add a sensor to the computation.

        Args:
            sensor: The sensor to add.
        """
        self._sensors.append(sensor)

        if self._use_shader:
            self._update_buffers_and_shaders()

    def _update_buffers_and_shaders(self) -> None:
        """
        Update GPU buffers and shaders.
        """
        (
            self._position_buffer,
            self._param_buffer,
            self._output_rays_buffer,
            self._inv_buffer,
        ) = self._generate_buffers()

        self._id_shader = self._generate_shaders()

    def update_sensors(self) -> None:
        """
        Update all sensors' hitpoints.
        """
        if not self._sensors:
            return

        self._id_view.update_and_draw_in_framebuffer(force=True)

        if self._use_shader:
            self._update_sensors_shaders()
        else:
            self._update_sensors_cpu()

    def _update_sensors_shaders(self) -> None:
        """
        Update sensors using GPU shaders.
        """
        update_inv = False
        for sensor in self._sensors:
            if sensor.require_invisible_update:
                update_inv = True

        if update_inv:
            self._update_buffers_and_shaders()

        self._position_buffer = self._ctx.buffer(
            data=array("f", self._generate_position_buffer())
        )
        self._position_buffer.bind_to_storage_buffer(binding=3)

        self._id_view.texture.use()
        self._id_shader.run(group_x=self._n_sensors)

        hitpoints = np.frombuffer(
            self._output_rays_buffer.read(), dtype=np.float32
        ).reshape(self._n_sensors, self._max_n_rays, 10)

        for index, sensor in enumerate(self._sensors):
            sensor.update_hitpoints(hitpoints[index, : sensor.resolution, :])

    def _update_sensors_cpu(self) -> None:
        """
        Updates the sensors' data using a CPU-based approach.

        This method processes the sensor data by calculating the hitpoints of rays
        cast by each sensor in the playground. It uses the ID views to
        determine the positions, distances, and other attributes of the detected
        objects.

        Steps:
        1. Retrieve the ID images from the views.
        2. For each sensor:
           - Calculate the start and end positions of the rays.
           - Clip the ray points to ensure they are within the view bounds.
           - Retrieve object IDs and filter out invisible objects.
           - Calculate the first hitpoint for each ray.
           - Compute relative positions and distances of the hitpoints.
           - Update the sensor with the calculated hitpoints.

        Notes:
        - This method is used when shaders are not enabled for sensor updates.
        - It handles invisible objects by removing their IDs from the results.
        """
        img_id = self._id_view.get_np_img()

        for sensor in self._sensors:
            # Calculate the start position of the rays in the view
            end_positions = sensor.end_positions
            ray_start_x = ((sensor.position[0] - self._id_view.center[0]) * self._id_view.zoom
                           + self._id_view.width / 2)
            ray_start_y = ((sensor.position[1] - self._id_view.center[1]) * self._id_view.zoom
                           + self._id_view.height / 2)
            center_on_view = np.asarray((ray_start_x, ray_start_y)).reshape(2, 1)

            # Calculate the end positions of the rays
            rays_end = center_on_view + end_positions * self._id_view.zoom

            # Generate points along the rays
            points = np.linspace(center_on_view, rays_end, num=sensor.n_points)

            # Clip points to ensure they are within the view bounds
            points[:, 0, :] = np.clip(points[:, 0, :], 0, self._id_view.width - 1)
            points[:, 1, :] = np.clip(points[:, 1, :], 0, self._id_view.height - 1)

            points = points.swapaxes(1, 2).reshape(-1, 2)
            rr, cc = points[:, 1].astype(int), points[:, 0].astype(int)

            # Retrieve object IDs from the ID image
            pts_ids = img_id[rr, cc].astype(np.uint64)
            ids = 256 * 256 * pts_ids[:, 2] + 256 * pts_ids[:, 1] + pts_ids[:, 0]

            # Remove invisible objects
            invisible_mask = ~np.isin(ids, sensor.invisible_ids)
            ids = ids * invisible_mask

            ids = ids.reshape(-1, sensor.resolution).transpose()

            # Find the first non-zero ID for each ray
            index_first_non_zero = np.argmax((ids != 0), axis=1)
            id_first_non_zero = ids[
                np.arange(len(index_first_non_zero)), index_first_non_zero
            ]

            # Calculate the hitpoints
            points = points.reshape((-1, sensor.resolution, 2))
            view_position = points[
                            index_first_non_zero, np.arange(len(index_first_non_zero)), :
                            ]

            # Calculate relative positions and distances
            rel_pos = center_on_view.transpose() - view_position
            distance = np.sqrt(rel_pos[:, 0] ** 2 + rel_pos[:, 1] ** 2)
            distance[id_first_non_zero == 0] = sensor.max_range
            distance = np.expand_dims(distance, -1)

            # Calculate absolute positions in the environment
            x_abs = ((view_position[:, 0] - self._id_view.width / 2) / self._id_view.zoom
                     + self._id_view.center[0])
            y_abs = ((view_position[:, 1] - self._id_view.height / 2) / self._id_view.zoom
                     + self._id_view.center[1])
            view_position[id_first_non_zero == 0, :] = rays_end[
                                                       :, id_first_non_zero == 0
                                                       ].T
            abs_env_position = np.vstack((x_abs, y_abs)).transpose()

            # Broadcast the center position to match the resolution
            center_on_view = np.broadcast_to(
                center_on_view.transpose(), (sensor.resolution, 2)
            )

            # Expand the ID array for concatenation
            id_first_non_zero = np.expand_dims(id_first_non_zero, -1)

            # Combine all hitpoint data
            hitpoints = np.hstack(
                (
                    view_position,
                    abs_env_position,
                    np.zeros((sensor.resolution, 2)),
                    center_on_view,
                    id_first_non_zero,
                    distance,
                )
            )

            # Update the sensor with the calculated hitpoints
            sensor.update_hitpoints(hitpoints)
