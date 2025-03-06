class DroneMessage:
    class Subject:
        MAPPING = "MAPPING"
        COMMUNICATION = "COMMUNICATION"
        CONTROL = "CONTROL"
        ALERT = "ALERT"
        PASS = "PASS"
        LOCK_WOUNDED = "LOCK_WOUNDED"

    def __init__(self, subject: str, arg, drone_id=None):
        if subject not in vars(DroneMessage.Subject).values():
            raise ValueError(f"Invalid subject: {subject}")
        

        self.subject = subject
        self.arg = arg
        self.drone_id = drone_id