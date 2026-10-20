from __future__ import annotations

from array import array
from os import path
from typing import Optional, Iterable, List

import arcade
import numpy as np

from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor
from swarm_rescue.simulation.ray_sensors.uid_provider import UidProvider


class RayCompute:
    """
    Class for computing ray-based ray_sensors hitpoints using shaders or CPU.

    The geometry comes from a `UidProvider`, not from a view: this class never
    creates, draws or knows about the presentation. Whoever owns the
    rendering (`Playground`) builds the uid view and hands it over.
    """

    def __init__(self, ctx, uid_provider: UidProvider, use_shader: bool = True):
        """
        Initialize RayCompute.

        `use_shader=False` selects a numpy reimplementation of the raycast. It
        is a **reference implementation, not a fallback**: measured on
        `MapFinal_2024_25_01` (10 drones, 20 sensors), it runs at 52.8 ms/step
        against 13.3 ms/step with the shaders, i.e. 4x slower. Turning the
        shaders off to "save time" is the opposite of what it does; keep it for
        `test_lidar_shader_vs_cpu_similarity`, which needs both paths.

        The gap is not the numpy work: the vector ops account for 4.4 ms of the
        48.2, the rest being per-sensor allocation on 35x200 arrays plus a
        6.3 ms GPU->CPU framebuffer read. So vectorizing the CPU path further
        would not close it; a CPU-only machine would need a rasterizer that does
        not go through the framebuffer at all.

        Args:
            ctx: The OpenGL context, used to allocate the shader buffers.
            uid_provider (UidProvider): Supplies the image in which each pixel
                holds the uid of the object drawn on it.
            use_shader (bool): Whether to use shaders for computation.
        """
        self._ctx = ctx

        self._use_shader = use_shader

        self._uid_provider = uid_provider

        self._sensors: List[RaySensor] = []

        if self._use_shader:
            self._view_params_buffer = self._ctx.buffer(
                data=array(
                    "f",
                    [
                        self._uid_provider.center[0],
                        self._uid_provider.center[1],
                        self._uid_provider.width,
                        self._uid_provider.height,
                        self._uid_provider.zoom,
                    ],
                )
            )

            self._view_params_buffer.bind_to_storage_buffer(binding=6)

            self._position_buffer: Optional[arcade.gl.Buffer] = None
            self._param_buffer: Optional[arcade.gl.Buffer] = None
            self._output_rays_buffer: Optional[arcade.gl.Buffer] = None
            self._inv_buffer: Optional[arcade.gl.Buffer] = None

            shader_dir = path.abspath(path.join(path.dirname(__file__), "shaders"))

            with open(path.join(shader_dir, "id_compute.glsl"), "rt", encoding="utf-8") as f_id:
                self._source_compute_ids = f_id.read()

            self._id_shader: Optional[arcade.gl.ComputeShader] = None

    @property
    def uid_provider(self) -> UidProvider:
        """
        The image the ray sensors read the entity uids from.

        Exposed so that the presentation can recognize this particular view and
        leave its sprite colors alone (see `DroneBase`): those colors *are*
        the uids, so swapping a sprite texture here would corrupt the physics.
        """
        return self._uid_provider

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

    def _generate_parameter_buffer(self) -> Iterable[float]:
        """
        Generate parameter buffer for all sensors.
        """
        for sensor in self._sensors:
            yield sensor.max_range
            yield sensor.fov
            yield sensor.resolution
            yield sensor.n_points

    def _generate_position_buffer(self) -> Iterable[float]:
        """
        Generate position buffer for all sensors.
        """
        for sensor in self._sensors:
            yield sensor.position[0]
            yield sensor.position[1]
            yield sensor.angle

    def _generate_output_buffer(self) -> Iterable[float]:
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

    def _generate_invisible_buffer(self) -> Iterable[int]:
        """
        Generate buffer for invisible elements for all sensors.
        """
        for sensor in self._sensors:

            count = 1
            uid = sensor.anchor.uid
            if uid is not None:
                yield uid

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
        if sensor in self._sensors:
            return

        self._sensors.append(sensor)

        if self._use_shader:
            self._update_buffers_and_shaders()

    def remove(self, sensor) -> None:
        """
        Remove a sensor from the computation.

        Args:
            sensor: The sensor to remove.
        """
        if sensor not in self._sensors:
            return

        self._sensors.remove(sensor)

        if self._use_shader and self._sensors:
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

        self._uid_provider.render_uids()

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

        self._uid_provider.bind_uid_texture()
        id_shader = self._id_shader
        output_rays_buffer = self._output_rays_buffer
        assert id_shader is not None and output_rays_buffer is not None
        id_shader.run(group_x=self._n_sensors)

        hitpoints = np.frombuffer(
            output_rays_buffer.read(), dtype=np.float32
        ).reshape(self._n_sensors, self._max_n_rays, 10)

        for index, sensor in enumerate(self._sensors):
            sensor.update_hitpoints(hitpoints[index,: sensor.resolution, :])

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
        - Measured at 48.2 ms/step for 20 sensors, against 1.7 ms/step for the
          shader path. It exists to be compared against, not to be run; see the
          `RayCompute.__init__` docstring before reaching for it.
        """
        img_id = self._uid_provider.read_uid_image()

        # `img_id` is a numpy array indexed from 0, while the world is centered on
        # the origin: `TopDownView` projects with `ortho(-w/2, w/2, -h/2, h/2)`, so
        # the world point (-w/2, -h/2) is pixel (0, 0). The offset below is that
        # constant origin shift, not a coordinate conversion.
        #
        # It cannot be dropped: a drone on the negative side of the map has
        # negative world coordinates, and numpy would read `img_id[-100]` as
        # `img_id[300]`, i.e. the opposite side of the image, with no error
        # raised. Measured on a drone at world (-150, -100), 252 of the 362
        # hitpoint coordinates are negative, so most rays would be sampled on the
        # wrong side.
        pixel_origin = np.array([self._uid_provider.width / 2,
                                 self._uid_provider.height / 2])

        for sensor in self._sensors:
            # Everything below is computed in WORLD coordinates. The rays are
            # built in world units and shifted to pixels once, at the lookup.
            end_positions = sensor.end_positions

            # Sensor position, in world units. `end_positions` is (2, resolution)
            # and already in world units, so nothing has to be converted here.
            center_world = np.asarray(
                (sensor.position[0], sensor.position[1]), dtype=float).reshape(2, 1)

            # End of each ray, in world units.
            rays_end = center_world + end_positions

            # Sample each ray at n_points steps, in world units.
            # Shapes: ratio (1, 1, n_points) and end_positions (2, resolution, 1),
            # so the product is (2, resolution, n_points); transposing it gives
            # (resolution, n_points, 2): one row per ray, (x, y) last.
            ratio = np.linspace(0.0, 1.0, num=sensor.n_points).reshape(1, 1, -1)
            offsets = (end_positions.reshape(2, -1, 1) * ratio).transpose(1, 2, 0)
            world = offsets + center_world.reshape(2, 1, 1).transpose(1, 2, 0)

            # World -> pixel: the origin shift, then clip to the image bounds.
            # `pixels` is (resolution, n_points, 2), the same layout as `world`.
            pixels = np.clip(world + pixel_origin, 0,
                             [self._uid_provider.width - 1,
                              self._uid_provider.height - 1])

            # One conversion for both axes rather than one per axis:
            # 0.059 ms -> 0.019 ms for a lidar. Same values -- the clip above
            # has already made every coordinate non-negative, so truncating
            # toward zero is the same as rounding down.
            pixel_index = pixels.astype(np.int32)
            rr, cc = pixel_index[:, :, 1], pixel_index[:, :, 0]

            # Retrieve object IDs from the ID image, keeping the
            # (resolution, n_points) layout.
            pts_ids = img_id[rr, cc].astype(np.uint64)
            ids = 256 * 256 * pts_ids[:, :, 2] + 256 * pts_ids[:, :, 1] + pts_ids[:, :, 0]

            # Remove invisible objects.
            #
            # A loop of comparisons rather than `np.isin`: these lists hold one
            # or two uids (the sensor's own anchor, plus a grasped entity), and
            # `isin` sorts its argument, which on a 54300-element array costs
            # more than the comparison itself -- 0.079 ms against 0.007 ms.
            # Above a handful of entries `isin` is kept, since its sort does
            # pay off there.
            invisible_ids = sensor.invisible_ids
            if len(invisible_ids) > 4:
                ids = ids * ~np.isin(ids, invisible_ids)
            else:
                for invisible_id in invisible_ids:
                    ids = ids * (ids != invisible_id)

            ids = ids.reshape(sensor.resolution, sensor.n_points)

            # Find the first non-zero ID for each ray
            index_first_non_zero = np.argmax((ids != 0), axis=1)
            id_first_non_zero = ids[
                np.arange(len(index_first_non_zero)), index_first_non_zero
            ]

            # The world position of the sample that produced that first id.
            # `world` is (resolution, n_points, 2) and `index_first_non_zero` is
            # per ray, so the ray index goes on axis 0 and the sample index on
            # axis 1 -- the same order the ids were read in.
            world_position = world[
                            np.arange(len(index_first_non_zero)), index_first_non_zero, :
                            ]

            # A ray that hit nothing is reported at its full range, so it ends at
            # `rays_end`. This happens before the concatenation because the
            # position stored in the hitpoints is `world_position`.
            world_position[id_first_non_zero == 0, :] = rays_end[
                                                        :, id_first_non_zero == 0
                                                        ].T

            # Distance, in world units between the sensor and the hitpoint: no
            # pixel round trip involved.
            rel_pos = center_world.transpose() - world_position
            distance = np.sqrt(rel_pos[:, 0] ** 2 + rel_pos[:, 1] ** 2)
            distance[id_first_non_zero == 0] = sensor.max_range
            distance = np.expand_dims(distance, -1)

            # The hitpoint is already in world units.
            abs_env_position = world_position

            # Sensor position in world units, broadcast to the resolution.
            center_world_broadcast = np.broadcast_to(
                center_world.transpose(), (sensor.resolution, 2)
            )

            # Expand the ID array for concatenation
            id_first_non_zero = np.expand_dims(id_first_non_zero, -1)

            # Combine all hitpoint data.
            #
            # Columns 0:2 and 2:4 are both the world position of the hitpoint.
            # They used to differ (0:2 in view pixels, 2:4 in world), and the
            # drawing code had to pick the right one. With a world-space uid
            # image they are the same value; both are kept so the output layout
            # stays identical to the shader's and to what the sensors read.
            hitpoints = np.hstack(
                (
                    world_position,
                    abs_env_position,
                    np.zeros((sensor.resolution, 2)),
                    center_world_broadcast,
                    id_first_non_zero,
                    distance,
                )
            )

            # Update the sensor with the calculated hitpoints
            sensor.update_hitpoints(hitpoints)
