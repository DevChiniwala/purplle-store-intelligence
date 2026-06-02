import yaml
import supervision as sv
import numpy as np

class ZoneClassifier:
    def __init__(self, camera_id: str, config_path: str):
        with open(config_path, "r") as f:
            cameras = yaml.safe_load(f)["cameras"]
        
        self.camera_id = camera_id
        if camera_id not in cameras:
            raise ValueError(f"Camera {camera_id} not found in config")
            
        self.zones = cameras[camera_id].get("zones", {})
        self.polygons = {}
        
        # Pre-compute supervision polygons
        # Original coordinates are normalized [0.0-1.0], scale to 1920x1080 for matching
        # (Assuming standard 1080p resolution)
        W, H = 1920, 1080
        for zone_id, zone_data in self.zones.items():
            pts = np.array(zone_data["polygon"])
            pts[:, 0] *= W
            pts[:, 1] *= H
            self.polygons[zone_id] = sv.PolygonZone(polygon=pts.astype(int))

    def get_zone_for_point(self, x: int, y: int) -> str | None:
        """Returns the first zone containing the point."""
        # This is a naive point-in-polygon check for bottom-center of bounding box
        point = np.array([[x, y]])
        for zone_id, polygon in self.polygons.items():
            # Trigger method takes Detections, but we can check raw point via trigger with fake detections
            # Or just use cv2.pointPolygonTest
            import cv2
            if cv2.pointPolygonTest(polygon.polygon, (x, y), False) >= 0:
                return zone_id
        return None
