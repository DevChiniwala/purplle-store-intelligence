import yaml
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EdgeCaseManager:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.settings = yaml.safe_load(f)
            
        self.staff_tracks = set()
        
        # Simple history for group detection (track_id -> last known position (x, y))
        self.track_positions: Dict[int, Tuple[int, int]] = {}
        # track_id -> group_id mapping
        self.track_groups: Dict[int, str] = {}
        
        # Configs
        pipe_cfg = self.settings.get("pipeline", {})
        self.group_proximity = pipe_cfg.get("group_proximity_pixels", 150)
        self.child_height_ratio = pipe_cfg.get("child_height_ratio", 0.6)

    def identify_staff(self, track_id: int, zone: str) -> bool:
        """Mark track as staff if they enter a staff_only zone."""
        # Note: In a full pipeline, we would also check total presence duration vs video length
        if "staff_only" in zone or "backroom" in zone.lower() or "storage" in zone.lower():
            self.staff_tracks.add(track_id)
            return True
        return track_id in self.staff_tracks

    def update_positions_and_groups(self, track_id: int, x_center: int, y_bottom: int) -> str:
        """Simple spatial clustering for groups"""
        self.track_positions[track_id] = (x_center, y_bottom)
        
        # Check if already in a group
        if track_id in self.track_groups:
            return self.track_groups[track_id]
            
        # Check distance to others
        for other_id, pos in self.track_positions.items():
            if other_id == track_id:
                continue
            
            # Calculate euclidian distance
            dist = ((pos[0] - x_center)**2 + (pos[1] - y_bottom)**2)**0.5
            if dist < self.group_proximity:
                # Join their group or create new one
                group_id = self.track_groups.get(other_id, f"grp_{other_id}_{track_id}")
                self.track_groups[track_id] = group_id
                self.track_groups[other_id] = group_id
                return group_id
                
        # No group
        return None
        
    def check_child(self, bbox: List[float], average_height: float = 600.0) -> bool:
        """Very rough heuristic for child detection based on bbox height"""
        height = bbox[3] - bbox[1]
        if height < (average_height * self.child_height_ratio):
            return True
        return False
