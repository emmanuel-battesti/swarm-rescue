import copy
import random
import time
import math
from typing import List, Optional, Union

import numpy as np
from enum import Enum

from spg_overlay.rescue_center import RescueCenter
from spg_overlay.wounded_person import WoundedPerson

from spg_overlay.drone import DroneAbstract
from spg_overlay.utils import sign, normalize_angle
from simple_playgrounds.common.entity import Entity


class MyDroneRescueWoundedPersons(DroneAbstract):
    class Activity(Enum):
        SEARCHING_WOUNDED = 1
        GRASPING_WOUNDED = 2
        SEARCHING_RESCUE_CENTER = 3
        DROPPING_AT_RESCUE_CENTER = 4
        RETURN_EMPTY_HAND = 5
        BLOCKED = 6

    def __init__(self,
                 identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)
        self.state = self.Activity.SEARCHING_WOUNDED
        self._counter = 0
        self._all_positions = list()
        self._path_to_rescue_center = list()
        self._path_to_last_person = list()

        self._counter_block = 0
        self._counter_unblock = 0

        self._threshold_block = 30
        self._threshold_unblock = 20

        self._previous_state = self.state
        self._alpha = 0
        self._block_grasping = 0

    def define_message(self):
        msg_data = (self.identifier, self.coordinates)
        return msg_data

    def control(self):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 1,
                   self.activate: 0}

        found_wounded, found_rescue_center, command_semantic = self.process_semantic_sensor(self.semantic_cones())
        # touched, command_touch = process_touch_sensor(self.touch())
        command_lidar = self.process_lidar_sensor(self.lidar())
        command_lidar2 = self.process_lidar_sensor2(self.lidar())
        beta = 0.0
        command_lidar[self.longitudinal_force] = \
            beta * command_lidar[self.longitudinal_force] \
            + (1 - beta) * command_lidar2[self.longitudinal_force]
        command_lidar[self.lateral_force] = \
            beta * command_lidar[self.lateral_force] \
            + (1 - beta) * command_lidar2[self.lateral_force]
        command_lidar[self.rotation_velocity] = \
            beta * command_lidar[self.rotation_velocity] \
            + (1 - beta) * command_lidar2[self.rotation_velocity]

        # touched = False

        self._counter += 1

        quasi_speed = max(abs(self.velocity[0]), abs(self.velocity[1]))
        # print(quasi_speed)
        if abs(quasi_speed) < 1.0:
            self._counter_block += 1
        else:
            self._counter_block = 0

        # print("_counter_block", self._counter_block, "_threshold_block", self._threshold_block)
        if self._counter_block > self._threshold_block and self.state is not self.Activity.BLOCKED:
            self._previous_state = self.state
            self.state = self.Activity.BLOCKED
            self._counter_unblock = 0
            # self._path_to_last_person.clear()
            # self._all_positions.clear()
            # self._path_to_rescue_center.clear()
            self._alpha = random.uniform(-math.pi, math.pi)
            self._rot = random.uniform(-1, 1)
            self._block_grasping = random.choices((0, 1))[0]

        #############
        # TRANSITIONS
        #############
        if self.is_holding_wrong(self.semantic_cones()):
            self.state = self.Activity.SEARCHING_WOUNDED
            self._path_to_last_person = copy.deepcopy(self._all_positions)
            self._all_positions.clear()
            self._counter_block = 0

        self._counter_unblock += 1
        # if self.state is self.Activity.BLOCKED:
        #     print("_counter_unblock", self._counter_unblock, "_threshold_unblock", self._threshold_unblock)
        if self.state is self.Activity.BLOCKED and self._counter_unblock > self._threshold_unblock:
            self.state = self._previous_state
            self._counter_block = 0
            self._counter_unblock = 0

        elif self.state is self.Activity.SEARCHING_WOUNDED and found_wounded:
            # print("change to GRASPING_WOUNDED")
            self.state = self.Activity.GRASPING_WOUNDED
            self._path_to_last_person.clear()
            self._counter_block = 0

        elif self.state is self.Activity.GRASPING_WOUNDED and self.grasp.is_holding:
            # print("change to SEARCHING_RESCUE_CENTER")
            self.state = self.state.SEARCHING_RESCUE_CENTER
            self._path_to_rescue_center = copy.deepcopy(self._all_positions)
            self._all_positions.clear()
            self._counter_block = 0

        elif self.state is self.Activity.GRASPING_WOUNDED and not found_wounded:
            # print("change to SEARCHING_WOUNDED")
            self.state = self.state.SEARCHING_WOUNDED
            self._path_to_rescue_center.clear()
            self._counter_block = 0

        elif self.state is self.Activity.SEARCHING_RESCUE_CENTER and found_rescue_center:
            # print("change to DROPPING_AT_RESCUE_CENTER")
            self.state = self.Activity.DROPPING_AT_RESCUE_CENTER

        # elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and found_rescue_center:
        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and not self.grasp.is_holding:
            # print("change to SEARCHING_WOUNDED")
            self.state = self.Activity.SEARCHING_WOUNDED
            self._path_to_last_person = copy.deepcopy(self._all_positions)
            self._all_positions.clear()
            self._counter_block = 0

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and not found_rescue_center:
            # print("change to SEARCHING_RESCUE_CENTER")
            self.state = self.Activity.SEARCHING_RESCUE_CENTER
            self._counter_block = 0

        ##########
        # COMMANDS
        ##########
        if self.state is self.Activity.SEARCHING_WOUNDED:
            ok, command_positions = self.process_positions_searching(self._path_to_last_person)
            if ok:
                command = command_positions
                # print(self.counter, "1 replay position")
            else:
                command = command_lidar
                # print(self.counter, "1 random with lidar")
            command[self.grasp] = 0
            # print("add positions")
            self._all_positions.append(self.position)

        elif self.state is self.Activity.GRASPING_WOUNDED:
            command = command_semantic
            command[self.grasp] = 1

        elif self.state is self.Activity.SEARCHING_RESCUE_CENTER:
            ok, command_positions = self.process_positions_searching(self._path_to_rescue_center)
            if ok:
                command = command_positions
                # print(self.counter, "2 replay position")
            else:
                command = command_lidar
                # print(self.counter, "2 random with lidar")
            command[self.grasp] = 1
            self._all_positions.append(self.position)

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER:
            command = command_semantic
            command[self.grasp] = 1

        elif self.state is self.Activity.BLOCKED:
            command = {self.longitudinal_force: math.cos(self._alpha),
                       self.lateral_force: math.sin(self._alpha),
                       self.rotation_velocity: self._rot,
                       self.grasp: self._block_grasping,
                       self.activate: 0}

        # elif touched:
        #     command = command_touch
        # if self.identifier == 1 or True:
        #     print(self.identifier, "state=", self.state, "holding=", self.grasp.is_holding, "grasping=",
        #           self.grasp.is_grasping)

        self.angle = normalize_angle(self.angle)

        found_collision, command_avoid_collision = self.process_avoid_collision()
        if found_collision:
            alpha = 0.75
            command[self.longitudinal_force] = \
                alpha * command_avoid_collision[self.longitudinal_force] \
                + (1 - alpha) * command[self.longitudinal_force]
            command[self.lateral_force] = \
                alpha * command_avoid_collision[self.lateral_force] \
                + (1 - alpha) * command[
                    self.lateral_force]

        return command

    def process_avoid_collision(self):
        command = {self.longitudinal_force: 0.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}
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

                dist_limit = 40
                d = distance - dist_limit
                intensity = 0
                if d < 0:
                    intensity = -1  # 2 / (1 + math.exp(-d / (dist_limit * 0.5))) - 1

                longi = intensity * math.cos(heading)
                lat = intensity * math.sin(heading)

                # if intensity != 0:
                #     print("dist", distance, "d", d, "intensity1", intensity)
                #     print("longi", longi, "lat", lat )

                if distance < dist_limit:
                    # heading < 0: a gauche
                    # heading > 0: a droite
                    # rotation_velocity : -1:gauche, 1:droite
                    command[self.longitudinal_force] = longi
                    command[self.lateral_force] = lat
                    # if heading > 0:
                    #     command[self.rotation_velocity] = -1.0
                    # else:
                    #     command[self.rotation_velocity] = 1.0
                    # command[self.longitudinal_force] = -1.0

                    found = True

                if found:
                    break
        return found, command

    def process_touch_sensor(self, the_touch_sensor):
        touched = False
        detection = max(the_touch_sensor.sensor_values)

        if detection > 0.5:

            indices = [i for i, x in enumerate(the_touch_sensor.sensor_values) if x == detection & 9 <= i < 27]

            if indices:
                touched = True

        command = {self.longitudinal_force: 1.0, self.rotation_velocity: 0.0, self.grasp: 0, self.activate: 0}

        return touched, command

    def is_holding_wrong(self, the_semantic_sensor):
        detection_semantic = the_semantic_sensor.sensor_values
        if self.state is self.Activity.SEARCHING_RESCUE_CENTER and detection_semantic:
            for detection in detection_semantic:
                if detection.entity and isinstance(detection.entity,
                                                   WoundedPerson) and detection.entity.held_by is not None:
                    if detection.distance < 20 and detection.entity.held_by != self:
                        return True

        return False

    def process_semantic_sensor(self, the_semantic_sensor):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 1,
                   self.activate: 0}
        rotation_velocity_max = 0.6

        current_time = time.time()
        if current_time % 3:
            rotation_velocity_max += 0.2
        detection_semantic = the_semantic_sensor.sensor_values
        best_angle = 1000
        found_wounded = False
        if (self.state is self.Activity.SEARCHING_WOUNDED
            or self.state is self.Activity.GRASPING_WOUNDED) \
                and detection_semantic:
            scores = []
            for detection in detection_semantic:
                # if detection.entity and isinstance(detection.entity,
                #                                    WoundedPerson) and detection.entity.held_by is not None:
                # print("held_by", detection.entity.held_by)

                if detection.entity \
                        and isinstance(detection.entity, WoundedPerson) \
                        and detection.entity.held_by is None:
                    # print("found WoundedPerson")
                    found_wounded = True
                    v = math.exp(-detection.angle * detection.angle) \
                        * math.exp(-detection.distance * detection.distance / 10 ** 5)
                    scores.append((v, detection.angle, detection.distance))

            best_score = -1
            for score in scores:
                if score[0] > best_score:
                    best_score = score[0]
                    best_angle = score[1]

        found_rescue_center = False
        if (self.state is self.Activity.SEARCHING_RESCUE_CENTER
            or self.state is self.Activity.DROPPING_AT_RESCUE_CENTER) \
                and detection_semantic:
            for detection in detection_semantic:
                if isinstance(detection.entity, RescueCenter):
                    # print("found RescueCenter")
                    found_rescue_center = True
                    best_angle = detection.angle

        if found_rescue_center or found_wounded:
            a = best_angle / math.pi  # a is between -1 and 1
            a = sign(a)
            command[self.rotation_velocity] = a * rotation_velocity_max

        return found_wounded, found_rescue_center, command

    def process_lidar_sensor(self, the_lidar_sensor):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 1,
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
        max_limit = [i * 400 / (size - 1) + 100 if i <= (size - 1) / 2
                     else i * -400 / (size - 1) + 500
                     for i in range(size)]

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
        # print("ray_angles_deg:")
        # print(ray_angles_deg)
        # print("ray_angles:")
        # print(ray_angles)
        # # print (detections)
        # plt.show()
        # plt.pause(0.001)
        # plt.clf()

        if found:
            command[self.rotation_velocity] = rotation_velocity * math.sin(far_angle)
            command[self.longitudinal_force] = math.cos(far_angle)

        if found and min_dist < 100:
            command[self.longitudinal_force] = min_dist / 100
            if near_angle > 0:
                command[self.rotation_velocity] = -rotation_velocity
            else:
                command[self.rotation_velocity] = rotation_velocity

        # Add some randomness
        r = random.choices([0, 1], weights=[10, 1])
        if r[0] == 1:
            command[self.rotation_velocity] = random.choices([-0.2, 0, 0.2])[0]

        return command

    def process_lidar_sensor2(self, the_lidar_sensor):
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 1,
                   self.activate: 0}
        rotation_velocity = 0.6

        detections = the_lidar_sensor.get_sensor_values()
        ray_angles = the_lidar_sensor.ray_angles
        size = the_lidar_sensor.size

        # print("****************")
        # found = False
        # best_angle = 0
        # max_dist = 0

        # Compute a shape of limit distance like ^
        # max_limit = [i * 400 / (size - 1) + 100 if i <= (size - 1) / 2 else i * -400 / (size - 1) + 500 for i in
        #              range(size)]

        list_zones = []
        threshold_zone = 290
        in_zone = False
        zone_angle = []
        found_zone = False
        while not found_zone:
            for i, detection in enumerate(detections):
                if not in_zone and detection >= threshold_zone:
                    found_zone = True
                    in_zone = True
                    zone_angle = [ray_angles[i]]
                elif in_zone and detection < threshold_zone:
                    in_zone = False
                    zone_angle.append(ray_angles[i])
                    list_zones.append(zone_angle)
            threshold_zone = threshold_zone - 20

        list_angles = []
        for i, zone_angle in enumerate(list_zones):
            a1 = normalize_angle(zone_angle[0])
            a2 = normalize_angle(zone_angle[1])
            mean_angle = math.atan2(0.5 * math.sin(a1) + 0.5 * math.sin(a2),
                                    0.5 * math.cos(a1) + 0.5 * math.cos(a2))
            list_angles.append(mean_angle)

        found = len(list_angles) > 0

        # ray_angles_deg = [angle / math.pi * 180 for angle in ray_angles]
        # plt.axis([-90, 90, 0, 300])
        # plt.ion()
        # plt.title("Lidar")
        # plt.xlabel("angle")
        # plt.ylabel("distance")
        # plt.plot(ray_angles_deg, detections)
        # print("ray_angles_deg:")
        # print(ray_angles_deg)
        # print("ray_angles:")
        # print(ray_angles)
        # # print (detections)
        # plt.show()
        # plt.pause(0.001)
        # plt.clf()

        if found:
            best_angle = min(list_angles, key=abs)
            # print(time.time(), "best_angle", best_angle)
            command[self.rotation_velocity] = rotation_velocity * math.sin(best_angle)
            command[self.longitudinal_force] = math.cos(best_angle)

        # Add some randomness
        r = random.choices([0, 1], weights=[10, 1])
        if r[0] == 1:
            command[self.rotation_velocity] = random.choices([-0.2, 0, 0.2])[0]

        return command

    def process_positions_searching(self, recorded_path):
        command_positions = {self.longitudinal_force: 0.0,
                             self.lateral_force: 0.0,
                             self.rotation_velocity: 0.0,
                             self.grasp: 0,
                             self.activate: 0}

        ok = False
        if recorded_path:
            # dist = 0
            # pt = self.position
            # dx, dy = 0, 0

            min_sqr_dist = 10 ** 10
            best_index = 0
            for i, pt in enumerate(recorded_path):
                dx = pt[0] - self.position[0]
                dy = pt[1] - self.position[1]
                sqr_dist = dx ** 2 + dy ** 2
                if min_sqr_dist > sqr_dist:
                    min_sqr_dist = sqr_dist
                    best_index = i

            # print("best_index before cut", best_index, "len(recorded_path) = ", len(recorded_path))

            # cut the end of the list
            cut_dist = 50
            if math.sqrt(min_sqr_dist) < cut_dist:
                sqr_dist = min_sqr_dist
                while math.sqrt(sqr_dist) < cut_dist and best_index > 0:
                    best_index -= 1
                    pt = recorded_path[best_index]
                    dx = pt[0] - self.position[0]
                    dy = pt[1] - self.position[1]
                    sqr_dist = dx ** 2 + dy ** 2

                if best_index == 0:
                    del recorded_path[:]
                else:
                    del recorded_path[best_index + 1:]

            # print("best_index", best_index, "len(recorded_path) = ", len(recorded_path))

            if recorded_path:
                dx = recorded_path[best_index][0] - self.position[0]
                dy = recorded_path[best_index][1] - self.position[1]

                # direction : absolute angle of the line between this drone and another drone
                direction = math.atan2(dy, dx)
                # heading : relative angle of another drone position from this drone
                heading = normalize_angle(direction - self.angle)

                command_positions[self.rotation_velocity] = math.sin(heading)
                command_positions[self.longitudinal_force] = math.cos(heading)
                command_positions[self.lateral_force] = math.sin(heading)

                ok = True

        return ok, command_positions

    # def entity_to_draw(self):
    #     list_element = list()
    #     for pt in self.all_positions:
    #         list_element.append()
