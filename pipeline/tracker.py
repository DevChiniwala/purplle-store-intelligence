import supervision as sv

class Tracker:
    def __init__(self, config_path: str):
        # We use ByteTrack from supervision
        self.tracker = sv.ByteTrack()

    def update(self, detections: sv.Detections) -> sv.Detections:
        # Update tracks based on current detections
        return self.tracker.update_with_detections(detections)
