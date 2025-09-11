import os
from typing import Tuple, List, Dict, Any, Optional
import yaml
from cerberus import Validator

from spg_overlay.entities.sensor_disablers import ZoneType

ZonesConfig = Tuple[ZoneType, ...]


class EvalConfig:
    """
    Une configuration d'évaluation :
        - une carte,
        - plusieurs zones de difficultés ou non (tuple de ZoneType)
        - nb de round
    """

    def __init__(self, map_name, zones_config: ZonesConfig = (), nb_rounds=1,
                 config_weight=1):
        self.zones_config = zones_config
        if self.zones_config is None:
            self.zones_config = ()
        self.map_name = map_name
        # self.map_name = map_type.__name__
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
    Liste de toutes les évaluations à faire, chaque évaluation est un
    EvalConfig
    """

    def __init__(self):
        self.list_eval_config = []
        self.list_weight = []
        self.sum_weight = 0
        self.config_description = dict()
        self.config_path = None  # Attribut pour stocker le chemin du fichier


    def add(self, eval_config: EvalConfig):
        self.list_eval_config.append(eval_config)
        self.list_weight.append(eval_config.config_weight)
        self.sum_weight += eval_config.config_weight
        id_config = len(self.list_eval_config)
        self.list_eval_config[-1].id_config = id_config
        self.config_description[id_config] = \
            (f"config {id_config} = "
             f"map {eval_config.map_name} +"
             f" zones \'{eval_config.zones_name_casual}\'")

    def reset(self):
        self.list_eval_config.clear()
        self.list_weight.clear()
        self.sum_weight = 0
        self.config_description.clear()

    def pretty_print(self):
        """
        Display the evaluation plan in a readable format, including the file name if provided.
        """
        if self.config_path:
            print(f"Evaluation Plan (from file: {os.path.basename(self.config_path)}):")
        else:
            print("Default Evaluation Plan (no file provided):")
        print("=" * 50)
        for eval_config in self.list_eval_config:
            print(f"Config ID: {eval_config.id_config}")
            print(f"  Map: {eval_config.map_name}")
            print(f"  Zones: {eval_config.zones_name_casual}")
            print(f"  Number of Rounds: {eval_config.nb_rounds}")
            print(f"  Weight: {eval_config.config_weight}")
            print("-" * 50)

    def from_yaml(self, config_path: str = None):
        """
        Create an EvalPlan instance from a YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file. If None, uses default config.

        Returns:
            An EvalPlan instance populated with configurations from the YAML file.
        """
        self.config_path = config_path  # Stocke le chemin du fichier

        # Load configurations from YAML
        eval_configs = self._load_from_yaml(config_path)
        if not eval_configs:
            return False

        # Convert zone names to enum values
        zone_types = {
            "NO_COM_ZONE": ZoneType.NO_COM_ZONE,
            "NO_GPS_ZONE": ZoneType.NO_GPS_ZONE,
            "KILL_ZONE": ZoneType.KILL_ZONE
        }

        # Add each configuration from the loaded YAML
        for config in eval_configs:
            # Get map class by name
            map_name = config["map_name"]
            if not map_name:
                print(f"Warning: Unknown map type '{map_name}', skipping configuration")
                continue

            # Process zones configuration
            zones_config = tuple()
            if "zones_config" in config and config["zones_config"]:
                zones_config = tuple(zone_types[zone] for zone in config["zones_config"] if zone in zone_types)

            # Create and add evaluation configuration
            eval_config = EvalConfig(
                map_name=map_name,
                zones_config=zones_config,
                nb_rounds=config.get("nb_rounds", 1),
                config_weight=config.get("config_weight", 1)
            )
            self.add(eval_config=eval_config)

        return True

    @staticmethod
    def _load_from_yaml(config_path: str = None) -> List[Dict[str, Any]]:
        """
        Load evaluation plan configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file. If None, uses default config.

        Returns:
            List of evaluation configurations
        """
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return []

        with open(config_path, 'r') as file:
            try:
                config = yaml.safe_load(file)
                if not EvalPlan._validate_yaml_config(config):
                    print("Invalid YAML configuration")
                    return []
                return config
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file: {e}")
                return []

    @staticmethod
    def _validate_yaml_config(config: List[Dict[str, Any]]) -> bool:
        """
        Validate the YAML configuration against the schema.

        Args:
            config: The loaded YAML configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        schema = {
            'map_name': {'type': 'string', 'required': True},
            'nb_rounds': {'type': 'integer', 'required': False, 'min': 1},
            'config_weight': {'type': 'integer', 'required': False, 'min': 1},
            'zones_config': {'type': 'list', 'schema': {'type': 'string'}, 'required': False}
        }

        v = Validator(schema)
        for item in config:
            if not v.validate(item):
                print(f"Validation error: {v.errors}")
                return False
        return True
