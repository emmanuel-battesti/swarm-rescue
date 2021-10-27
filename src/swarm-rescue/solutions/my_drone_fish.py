import random
import math
from copy import deepcopy
from typing import Optional

import numpy as np

from spg_overlay.drone import DroneAbstract
from spg_overlay.utils import normalize_angle


class MyDroneFish(DroneAbstract):
    def __init__(self, identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)

    def define_message(self):
        msg_data = (self.identifier, self.coordinates)
        return msg_data

    def control(self):
        command = {self.longitudinal_force: 0.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}

        command_lidar, collision_lidar = self.process_lidar_sensor(self.lidar())
        # if command_lidar[self.rotation_velocity] != 0:
        #     return command_lidar

        self.angle = normalize_angle(self.angle)

        found, command_comm = self.process_communication_sensor()

        alpha = 0.4  # 0.4
        alpha_rot = 0.75  # 0.75
        # if not found:
        #     print("Not found !")
        #     alpha = 0
        #     alpha_rot = 0

        if collision_lidar:
            # print("Collision !")
            alpha_rot = 0.1

        command[self.longitudinal_force] = \
            alpha * command_comm[self.longitudinal_force] \
            + (1 - alpha) * command_lidar[self.longitudinal_force]
        command[self.lateral_force] = \
            alpha * command_comm[self.lateral_force] \
            + (1 - alpha) * command_lidar[self.lateral_force]
        command[self.rotation_velocity] = \
            alpha_rot * command_comm[self.rotation_velocity] \
            + (1 - alpha_rot) * command_lidar[self.rotation_velocity]

        # print("command[self.rotation_velocity]", command[self.rotation_velocity])

        return command

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

        collision = False
        if found and min_dist < 50:
            collision = True
            if near_angle > 0:
                command[self.rotation_velocity] = -rotation_velocity
            else:
                command[self.rotation_velocity] = rotation_velocity

        # Add some randomness
        r = random.choices([0, 1], weights=[10, 1])
        if r[0] == 1:
            command[self.rotation_velocity] = random.choices([-1, 0, 1])[0]

        # command = {self.grasp: 0, self.longitudinal_force: 1.0, self.rotation_velocity: 0.0}
        return command, collision

    def process_communication_sensor(self):
        found = False
        command_comm = {self.longitudinal_force: 0.0,
                        self.lateral_force: 0.0,
                        self.rotation_velocity: 0.0,
                        self.grasp: 0,
                        self.activate: 0}

        if self.communication:
            received_messages = self.communication.received_message
            nearest_drone_coordinate1 = ((self.position[0], self.position[1]), self.angle)
            nearest_drone_coordinate2 = deepcopy(nearest_drone_coordinate1)

            min_dist1 = 10000
            min_dist2 = 10000
            # id_drone1 = 0
            # id_drone2 = 0
            diff_angle = 0

            for msg in received_messages:
                # communication = msg[0]
                message = msg[1]
                # id_drone = message[0]
                coordinate = message[1]
                (other_position, other_angle) = coordinate

                dx = other_position[0] - self.position[0]
                dy = other_position[1] - self.position[1]
                distance = math.sqrt(dx ** 2 + dy ** 2)

                # direction : absolute angle of the line between this drone and another drone
                direction = math.atan2(dy, dx)
                # heading : relative angle of another drone position from this drone
                heading = normalize_angle(direction - self.angle)

                # if another drone is near and in front
                if abs(heading) < math.pi / 1:
                    if distance < min_dist1:
                        min_dist2 = min_dist1
                        # id_drone2 = id_drone1
                        min_dist1 = distance
                        # id_drone1 = id_drone
                        nearest_drone_coordinate2 = nearest_drone_coordinate1
                        nearest_drone_coordinate1 = coordinate
                        found = True
                    elif distance < min_dist2 and distance != min_dist1:
                        min_dist2 = distance
                        # id_drone2 = id_drone
                        nearest_drone_coordinate2 = coordinate

            if not found:
                return found, command_comm

            if found and len(received_messages) >= 2:
                (nearest_position1, nearest_angle1) = nearest_drone_coordinate1
                (nearest_position2, nearest_angle2) = nearest_drone_coordinate2
                diff_angle1 = normalize_angle(nearest_angle1 - self.angle)
                diff_angle2 = normalize_angle(nearest_angle2 - self.angle)
                diff_angle = math.atan2(0.5 * math.sin(diff_angle1) + 0.5 * math.sin(diff_angle2),
                                        0.5 * math.cos(diff_angle1) + 0.5 * math.cos(diff_angle2))

            elif found and len(received_messages) >= 1:
                (nearest_position1, nearest_angle1) = nearest_drone_coordinate1
                diff_angle1 = normalize_angle(nearest_angle1 - self.angle)
                diff_angle = diff_angle1

            # si on est loin on se rapproche
            # heading < 0: a gauche
            # heading > 0: a droite
            # rotation_velocity : -1:gauche, 1:droite
            # on essaie de s'aligner : diff_angle -> 0
            command_comm[self.rotation_velocity] = math.sin(diff_angle)

            dist_limit = 60

            d1x = nearest_position1[0] - self.position[0]
            d1y = nearest_position1[1] - self.position[1]
            distance1 = math.sqrt(d1x ** 2 + d1y ** 2)

            d1 = distance1 - dist_limit
            intensity1 = 2 / (1 + math.exp(-d1 / (dist_limit * 0.5))) - 1

            direction1 = math.atan2(d1y, d1x)
            heading1 = normalize_angle(direction1 - self.angle)

            longi1 = intensity1 * math.cos(heading1)
            lat1 = intensity1 * math.sin(heading1)
            # print("dist", distance1, "intensity1", intensity1)

            if found and len(received_messages) == 1:
                command_comm[self.longitudinal_force] = longi1
                command_comm[self.lateral_force] = lat1

            elif found and len(received_messages) >= 2:
                d2x = nearest_position2[0] - self.position[0]
                d2y = nearest_position2[1] - self.position[1]
                distance2 = math.sqrt(d2x ** 2 + d2y ** 2)

                d2 = distance2 - dist_limit
                intensity2 = 2 / (1 + math.exp(-d2 / (dist_limit * 0.5))) - 1

                direction2 = math.atan2(d2y, d2x)
                heading2 = normalize_angle(direction2 - self.angle)

                longi2 = intensity2 * math.cos(heading2)
                lat2 = intensity2 * math.sin(heading2)

                command_comm[self.longitudinal_force] = 0.5 * (longi1 + longi2)
                command_comm[self.lateral_force] = 0.5 * (lat1 + lat2)

        return found, command_comm
