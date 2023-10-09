from typing import Tuple

from spg_overlay.entities.sensor_disablers import ZoneType

ZonesConfig = Tuple[ZoneType, ...]


class EvalConfig:
    """
    Une configuration d'évaluation :
        - une carte,
        - plusieurs zones de difficultés ou non (tuple de ZoneType)
        - nb de round
    """

    def __init__(self, map_type, zones_config: ZonesConfig = (), nb_rounds=1, config_weight=1):
        self.zones_config = zones_config
        if self.zones_config is None:
            self.zones_config = ()
        self.map_type = map_type
        self.map_name = map_type.__name__
        self.nb_rounds = nb_rounds
        self.config_weight = config_weight
        zone_name_list = []
        for zone in self.zones_config:
            zone_name_list.append(zone.name.lower())
        if not zone_name_list:
            zone_name_list.append("none")
        self.zones_name_for_filename = '__'.join(zone_name_list)
        self.zones_name_casual = ', '.join(zone_name_list)
        self.id_config = 1


class EvalPlan:
    """
    Liste de toutes les évaluations à faire, chaque évaluation est un EvalConfig
    """

    def __init__(self):
        self.list_eval_config = []
        self.list_weight = []
        self.sum_weight = 0
        self.config_description = dict()

    def add(self, eval_config: EvalConfig):
        self.list_eval_config.append(eval_config)
        self.list_weight.append(eval_config.config_weight)
        self.sum_weight += eval_config.config_weight
        id_config = len(self.list_eval_config)
        self.list_eval_config[-1].id_config = id_config
        self.config_description[id_config] = (f"config {id_config} = "
                                              f"map {eval_config.map_name} + zones \'{eval_config.zones_name_casual}\'")

    def reset(self):
        self.list_eval_config.clear()
        self.list_weight.clear()
        self.sum_weight = 0
        self.config_description.clear()
