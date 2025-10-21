import os
from typing import Tuple, List, Dict, Any, Optional

import yaml
from cerberus import Validator

from swarm_rescue.simulation.elements.sensor_disablers import ZoneType

ZonesConfig = Tuple[ZoneType, ...]


class EvalConfig:
    """
    Evaluation configuration for a simulation round.

    Attributes:
        map_name (str): Name of the map.
        zones_config (ZonesConfig): Tuple of ZoneType for special zones.
        nb_rounds (int): Number of rounds.
        config_weight (int): Weight for this configuration.
        zones_name_for_filename (str): String for filename usage.
        zones_name_casual (str): Human-readable string for zones.
        id_config (int): Unique identifier for the configuration.
    """

    def __init__(self, map_name: str, zones_config: ZonesConfig = (), nb_rounds: int = 1,
                 config_weight: int = 1):
        """
        Initialize an EvalConfig.

        Args:
            map_name (str): Name of the map.
            zones_config (ZonesConfig): Tuple of ZoneType for special zones.
            nb_rounds (int): Number of rounds.
            config_weight (int): Weight for this configuration.
        """
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
    List of all evaluation configurations to be executed.

    Attributes:
        list_eval_config (List[EvalConfig]): List of evaluation configs.
        list_weight (List[int]): List of config weights.
        sum_weight (int): Sum of all config weights.
        config_description (dict): Description of each config.
        config_path (Optional[str]): Path to the YAML config file.
    """

    def __init__(self):
        """
        Initialize an EvalPlan.
        """
        self.list_eval_config = []
        self.list_weight = []
        self.sum_weight = 0
        self.config_description = dict()
        self.config_path = None  # Attribut pour stocker le chemin du fichier
        self.stat_saving_enabled = False  # Default value, can be overridden by YAML
        self.video_capture_enabled = False  # Default value, can be overridden by YAML

    def add(self, eval_config: EvalConfig) -> None:
        """
        Add an EvalConfig to the plan.

        Args:
            eval_config (EvalConfig): The configuration to add.
        """
        self.list_eval_config.append(eval_config)
        self.list_weight.append(eval_config.config_weight)
        self.sum_weight += eval_config.config_weight
        id_config = len(self.list_eval_config)
        self.list_eval_config[-1].id_config = id_config
        self.config_description[id_config] = \
            (f"config {id_config} = "
             f"map {eval_config.map_name} +"
             f" zones \'{eval_config.zones_name_casual}\'")

    def reset(self) -> None:
        """
        Reset the evaluation plan.
        """
        self.list_eval_config.clear()
        self.list_weight.clear()
        self.sum_weight = 0
        self.config_description.clear()

    def pretty_print(self) -> None:
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

    def from_yaml(self, config_path: Optional[str] = None) -> bool:
        """
        Create an EvalPlan instance from a YAML configuration file.

        Args:
            config_path (Optional[str]): Path to the YAML configuration file. If None, uses default config.

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        self.config_path = config_path  # Store the file path

        # Load configurations from YAML
        config = self._load_from_yaml(config_path)
        if not config:
            return False

        # Expect top-level dict with 'stat_saving_enabled' and 'evaluation_plan'
        if not isinstance(config, dict) or 'evaluation_plan' not in config:
            print("Invalid YAML structure: missing 'evaluation_plan' list.")
            return False

        self.stat_saving_enabled = config.get('stat_saving_enabled', True)
        self.video_capture_enabled = config.get('video_capture_enabled', False)
        eval_configs = config['evaluation_plan']

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
    def _load_from_yaml(config_path: Optional[str] = None) -> dict:
        """
        Load evaluation plan configuration from a YAML file.

        Args:
            config_path (Optional[str]): Path to the YAML configuration file. If None, uses default config.

        Returns:
            dict: Loaded configuration data.
        """
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return {}
        with open(config_path, 'r') as file:
            try:
                config = yaml.safe_load(file)
                return config
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file: {e}")
                return {}
