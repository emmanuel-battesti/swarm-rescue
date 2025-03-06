import numpy as np
from typing import List
from spg_overlay.entities.wounded_person import WoundedPerson
from solutions.utils.pose import Position
from solutions.utils.dataclasses_config import TrackingParams

class TrackedWounded:
    """Stores encountered wounded person informations. Positions are in WORLD COORDINATES"""
    def __init__(self, position, rescued=False):
        self.position = position
        self.rescued = rescued

class TrackedNoComZone:
    """
    CHATGPT GENERATED
    
    Stores encountered no communication zone informations. Positions are in WORLD COORDINATES"""
    def __init__(self, position):
        self.position = position

class ExplorationTracker:
    """
    Stores important information encountered during map exploration.
    Wounded persons, no_com_zones, etc...
    Positions are in WORLD COORDINATES
    """
    def __init__(self):
        self.wounded_persons: List[TrackedWounded] = []
        self.no_com_zones: List[TrackedNoComZone] = []

    def identify_wounded(self, wounded_sighting_position):
        """
        If there are wounded persons tracked in self.wounded_persons that are close enough to the wounded sighting position,
        return the closest one.
        Else return None.
        This function tackles the issue that we can't give global id to wounded persons, therefore we need to identify them through their position.
        """
        if not self.wounded_persons:
            return None
    
        closest_wounded = min(self.wounded_persons, 
                            key=lambda w: np.linalg.norm(np.array(w.position) - np.array(wounded_sighting_position)))
        
        # Check if within threshold distance
        if np.linalg.norm(np.array(closest_wounded.position) - np.array(wounded_sighting_position)) <= TrackingParams.wounded_id_distance_threshold:
            return closest_wounded

    def add_wounded(self, wounded_sighting_position):
        self.wounded_persons.append(TrackedWounded(wounded_sighting_position))

    def remove_wounded(self, wounded_sighting_position):
        wounded = self.identify_wounded(wounded_sighting_position)
        if wounded is None:
            return None
        else:
            self.wounded_persons.remove(wounded)

    def are_there_unrescued_wounded(self):
        return any([not w.rescued for w in self.wounded_persons])
    
    def add_no_com_zone(self, position):
        """
        CHATGPT GENERATED

        Add a no communication zone position"""
        self.no_com_zones.append(position)