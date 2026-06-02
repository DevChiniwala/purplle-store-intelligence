import cv2
import logging
from datetime import datetime, timezone
from .detector import Detector
from .tracker import Tracker
from .zone_classifier import ZoneClassifier
from .event_generator import EventGenerator
from .edge_cases import EdgeCaseManager
from events.publisher import EventPublisher

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, camera_id: str, video_path: str, config_path: str, camera_config_path: str):
        self.camera_id = camera_id
        self.video_path = video_path
        
        self.detector = Detector(config_path)
        self.tracker = Tracker(config_path)
        self.zone_classifier = ZoneClassifier(camera_id, camera_config_path)
        self.edge_case_manager = EdgeCaseManager(config_path)
        
        redis_url = "redis://redis:6379"  # in a real app, read from config
        self.event_generator = EventGenerator(EventPublisher(redis_url=redis_url))
        
    def process(self):
        logger.info(f"Starting processing for {self.camera_id}: {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {self.video_path}")
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"{self.camera_id} - FPS: {fps}, Total Frames: {frame_count}")
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Simulate real-time timestamps
            current_time = datetime.now(timezone.utc)
                
            # Process every 15 frames (~2 fps)
            if frame_idx % 15 == 0:
                detections = self.detector.detect(frame)
                tracked_detections = self.tracker.update(detections)
                
                for i in range(len(tracked_detections)):
                    bbox = tracked_detections.xyxy[i]
                    track_id = tracked_detections.tracker_id[i]
                    confidence = tracked_detections.confidence[i]
                    x_center = int((bbox[0] + bbox[2]) / 2)
                    y_bottom = int(bbox[3])
                    
                    zone = self.zone_classifier.get_zone_for_point(x_center, y_bottom)
                    
                    if zone:
                        # Process Edge Cases
                        is_staff = self.edge_case_manager.identify_staff(int(track_id), zone)
                        group_id = self.edge_case_manager.update_positions_and_groups(int(track_id), x_center, y_bottom)
                        is_child = self.edge_case_manager.check_child(bbox)
                        
                        metadata = {}
                        if is_child:
                            metadata["demographics"] = "child"
                        if group_id:
                            metadata["group_id"] = group_id
                            
                        # Generate semantic event
                        self.event_generator.generate_event(
                            camera_id=self.camera_id,
                            track_id=int(track_id),
                            zone=zone,
                            confidence=float(confidence),
                            timestamp=current_time,
                            is_staff=is_staff,
                            metadata=metadata
                        )
                        
            frame_idx += 1
            
        cap.release()
        logger.info(f"Finished processing {self.camera_id}")
