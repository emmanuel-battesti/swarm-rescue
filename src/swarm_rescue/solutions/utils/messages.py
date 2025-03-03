class DroneMessage:
    class Subject:
        MAPPING = "MAPPING"
        COMMUNICATION = "COMMUNICATION"
        CONTROL = "CONTROL"
        ALERT = "ALERT"
    
    class Code:
        LINE = "LINE"
        POINTS = "POINTS"

    def __init__(self, subject: str, code: str, arg, drone_id=None):
        if subject not in vars(DroneMessage.Subject).values():
            raise ValueError(f"Invalid subject: {subject}")
        if code not in vars(DroneMessage.Code).values():
            raise ValueError(f"Invalid code: {code}")

        self.subject = subject
        self.code = code
        self.arg = arg
        self.drone_id = drone_id