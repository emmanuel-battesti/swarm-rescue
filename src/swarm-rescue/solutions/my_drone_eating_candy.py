import random
import math
from typing import Optional

import numpy as np

from spg_overlay.drone import DroneAbstract
from spg_overlay.utils import normalize_angle

from simple_playgrounds.elements.collection.contact import Candy


class MyDroneEatingCandy(DroneAbstract):
    def __init__(self, identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)

    def define_message(self):
        msg_data = (self.identifier, self.coordinates)
        return msg_data

    def control(self):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}

        found, command_semantic = self.process_semantic_sensor(self.semantic_cones())
        # touched, command_touch = process_touch_sensor(self.touch())
        command_lidar = self.process_lidar_sensor(self.lidar())

        touched = False

        if not found and not touched:
            command = command_lidar
            # print("lidar")
        elif found:
            command = command_semantic
            # print("semantic")
        # elif touched:
        #     command = command_touch

        self.angle = normalize_angle(self.angle)

        if self.communication:
            received_messages = self.communication.received_message
            found = False
            for msg in received_messages:
                # communication = msg[0]
                message = msg[1]
                # id_drone = message[0]
                coordinate = message[1]
                (position, angle) = coordinate

                # distance = math.dist(coordinate[0], self.position)
                dx = position[0] - self.position[0]
                dy = position[1] - self.position[1]
                distance = math.sqrt(dx ** 2 + dy ** 2)

                direction = math.atan2(dy, dx)
                heading = normalize_angle(direction - self.angle)

                if distance < 100 and abs(heading) < math.pi / 2.:
                    # heading < 0: a gauche
                    # heading > 0: a droite
                    # rotation_velocity : -1:gauche, 1:droite
                    if heading > 0:
                        command[self.rotation_velocity] = -1.0
                    else:
                        command[self.rotation_velocity] = 1.0
                    # command[self.longitudinal_force] = -1.0
                    found = True

                if found:
                    break

        return command

    def process_touch_sensor(self, the_touch_sensor):
        touched = False
        detection = max(the_touch_sensor.sensor_values)

        if detection > 0.5:

            indices = [i for i, x in enumerate(the_touch_sensor.sensor_values) if x == detection & 9 <= i < 27]

            if indices:
                touched = True

        command = {self.longitudinal_force: 1.0, self.rotation_velocity: 0.0, self.grasp: 0, self.activate: 0}

        return touched, command

    def process_semantic_sensor(self, the_semantic_sensor):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}

        detection_semantic = the_semantic_sensor.sensor_values
        best_angle = 1000
        # min_dist = 10000
        found = False
        if detection_semantic:
            scores = []
            for detection in detection_semantic:
                if isinstance(detection.entity, Candy):
                    found = True
                    v1 = math.exp(-(detection.angle / (math.pi / 2)) ** 2)
                    v2 = math.exp(-(detection.distance / 100) ** 2)
                    v = v1 * v2
                    # print("angle=", detection.angle, "v1=", v1, "d=", detection.distance, "v2=", v2, "v=", v)
                    scores.append((v, detection.angle, detection.distance))

            best_score = -1
            for score in scores:
                if score[0] > best_score:
                    best_score = score[0]
                    best_angle = score[1]
                    # min_dist = score[2]

        # print("best d=", min_dist, "angle=", best_angle, "found=", found)

        if found:
            # best_angle : relative angle of another drone position from this drone
            command[self.rotation_velocity] = math.sin(best_angle)
            command[self.longitudinal_force] = math.cos(best_angle)
            command[self.lateral_force] = math.sin(best_angle)

        return found, command

    def process_lidar_sensor(self, the_lidar_sensor):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}
        rotation_velocity = 0.6

        detections = the_lidar_sensor.get_sensor_values()
        ray_angles = the_lidar_sensor.ray_angles
        size = the_lidar_sensor.size

        # print("****************")
        found = False
        # best_angle = 0
        # max_dist = 0

        # Compute a shape of limit distance like ^
        max_limit = [i * 400 / (size - 1) + 100 if i <= (size - 1) / 2 else i * -400 / (size - 1) + 500 for i in
                     range(size)]

        far_angle_raw = 0
        near_angle_raw = 0
        min_dist = 1000
        if size != 0:
            found = True
            # max_dist = max(detections)
            far_angle_raw = ray_angles[np.argmax(detections)]
            min_dist = min(detections)
            near_angle_raw = ray_angles[np.argmin(detections)]

        far_angle = far_angle_raw
        if abs(far_angle) < 1 / 180 * np.pi:
            far_angle = 0.0

        near_angle = near_angle_raw

        far_angle = normalize_angle(far_angle)
        # print("max_dist", max_dist, "far_angle_raw", far_angle_raw / np.pi * 180, "far_angle", far_angle / np.pi * 180)

        # ray_angles_deg = [angle / math.pi * 180 for angle in ray_angles]
        # plt.axis([-90, 90, 0, 300])
        # plt.ion()
        # plt.title("Lidar")
        # plt.xlabel("angle")
        # plt.ylabel("distance")
        # plt.plot(ray_angles_deg, detections)
        # plt.show()
        # plt.pause(0.001)
        # plt.clf()

        if found:
            if far_angle > 0:
                command[self.rotation_velocity] = rotation_velocity
            elif far_angle == 0:
                command[self.rotation_velocity] = 0
            else:
                command[self.rotation_velocity] = -rotation_velocity

        if found and min_dist < 100:
            if near_angle > 0:
                command[self.rotation_velocity] = -rotation_velocity
            else:
                command[self.rotation_velocity] = rotation_velocity

        # Add some randomness
        r = random.choices([0, 1], weights=[10, 1])
        if r[0] == 1:
            command[self.rotation_velocity] = random.choices([-1, 0, 1])[0]

        # command = {self.grasp: 0, self.longitudinal_force: 1.0, self.rotation_velocity: 0.0}
        return command
