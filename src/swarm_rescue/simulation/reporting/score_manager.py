class ScoreManager:
    """
    Tool to compute the final score in a drone rescue simulation.

     It takes into account the number of drones, time
     limits, and the number of wounded persons to calculate the score based on
     rescue percentage, exploration score, health returned and time taken to
     rescue all the wounded persons.

    Attributes:
        number_drones (int): Number of drones in the map.
        max_timestep_limit (int): Max number of timesteps.
        max_walltime_limit (int): Max wall time in seconds.
        total_number_wounded_persons (int): Number of wounded persons to rescue.
        w_rescue (float): Weight for rescue score.
        w_exploration (float): Weight for exploration score.
        w_score_health_returned (float): Weight for health return score.
        w_time (float): Weight for time score.
    """

    def __init__(self,
                 number_drones: int,
                 max_timestep_limit: int,
                 max_walltime_limit: int,
                 total_number_wounded_persons: int):
        """
        Initialize the ScoreManager.

        Args:
            number_drones (int): Number of drones.
            max_timestep_limit (int): Max timesteps.
            max_walltime_limit (int): Max wall time in seconds.
            total_number_wounded_persons (int): Number of wounded persons.
        """

        # 'number_drones' is the number of drones that will be generated in the
        # map
        self.number_drones = number_drones

        # 'max_timestep_limit' is the number of timesteps after which the
        # session will end.
        self.max_timestep_limit = max_timestep_limit

        # 'max_walltime_limit' is the elapsed time (in seconds) after which the
        # session will end.
        self.max_walltime_limit = max_walltime_limit

        # 'number_wounded_persons' is the number of wounded persons that should
        # be retrieved by the drones.
        self.total_number_wounded_persons = total_number_wounded_persons

        # weight for the different parts of the score. The sum must be equal
        # to 1.
        self.w_rescue = 0.5
        self.w_exploration = 0.2
        self.w_score_health_returned = 0.2
        self.w_time = 0.1

    def compute_score(self, number_rescued_persons: int, score_exploration: float,
                      score_health_returned: float, full_rescue_timestep: int) -> tuple:
        """
        Compute the final score out of 100.

        Args:
            number_rescued_persons (int): Number of rescued persons.
            score_exploration (float): Exploration score.
            score_health_returned (float): Health return score.
            full_rescue_timestep (int): Timesteps used to rescue all wounded.

        Returns:
            tuple: (score, percentage_rescue, score_timestep)
        """
        if self.total_number_wounded_persons > 0:
            percentage_rescue = (number_rescued_persons /
                                 self.total_number_wounded_persons * 100.0)
        else:
            percentage_rescue = 100.0

        if (number_rescued_persons == self.total_number_wounded_persons
                and score_exploration > 97):
            full_rescue_timestep = min(full_rescue_timestep,
                                       self.max_timestep_limit)
            score_timestep = ((self.max_timestep_limit - full_rescue_timestep)
                              / self.max_timestep_limit * 100.0)
        else:
            score_timestep = 0

        score = self.w_rescue * percentage_rescue + \
                self.w_exploration * score_exploration + \
                self.w_score_health_returned * score_health_returned + \
                self.w_time * score_timestep

        return score, percentage_rescue, score_timestep