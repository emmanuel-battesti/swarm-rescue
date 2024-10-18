class ScoreManager:
    """
     The ScoreManager class is a tool used to compute the final score in a
     drone rescue simulation. It takes into account the number of drones, time
     limits, and the number of wounded persons to calculate the score based on
     rescue percentage, exploration score, health returned and time taken to
     rescue all the wounded persons.

     Attributes:
        number_drones: The number of drones that will be generated in the map.
        max_timestep_limit: The number of time steps after which the session will
        end.
        max_walltime_limit: The elapsed time (in seconds) after which the session
        will end.
        total_number_wounded_persons: The number of wounded persons that should
        be retrieved by the drones.
        w_rescue: Weight for the rescue part of the score.
        w_exploration: Weight for the exploration part of the score.
        w_score_health_returned : Weight for the quantity of health of the
        drones returned to the "return area"
        w_time: Weight for the time part of the score.
    """

    def __init__(self,
                 number_drones: int,
                 max_timestep_limit: int,
                 max_walltime_limit: int,
                 total_number_wounded_persons: int):

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

    def compute_score(self, number_rescued_persons, score_exploration,
                      score_health_returned, full_rescue_timestep):
        """
        Compute the final score out of 100.
        Needed information :
            'number_rescued_persons': number of rescued persons by the drones
            'score_exploration': score of exploration computed by the
             exploredMap class
            'score_health_returned': score of health of the drones returned
             to the "return area"
            'full_rescue_timestep': number of timesteps used by the time all
            the wounded person are saved
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
