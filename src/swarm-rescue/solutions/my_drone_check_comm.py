import math
from typing import Optional

from spg_overlay.drone import DroneAbstract
from spg_overlay.utils import normalize_angle


class MyDroneCheckComm(DroneAbstract):
    def __init__(self, identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)

    def define_message(self):
        msg_data = (self.identifier, self.coordinates)
        return msg_data

    def control(self):
        command = {self.longitudinal_force: 0.0, self.rotation_velocity: 0.0, self.grasp: 0, self.activate: 0}

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
                print("distance", distance, "direction", direction, "heading", heading)

                if distance < 100 and abs(heading) < math.pi / 2.:
                    # heading < 0: a gauche
                    # heading > 0: a droite
                    # rotation_velocity : -1:gauche, 1:droite
                    if heading > 0:
                        command[self.rotation_velocity] = -1.0
                    else:
                        command[self.rotation_velocity] = 1.0
                    command[self.longitudinal_force] = -1.0
                    found = True

                if found:
                    break

        return command
