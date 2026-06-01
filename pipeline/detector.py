import cv2
import yaml
from pathlib import Path
from ultralytics import YOLO
import supervision as sv
import numpy as np

class Detector:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        model_path = self.config["pipeline"]["detection_model"]
        self.model = YOLO(model_path)
        self.confidence = self.config["pipeline"]["detection_confidence"]
        self.classes = self.config["pipeline"]["detection_classes"]

    def detect(self, frame: np.ndarray) -> sv.Detections:
        # Run YOLO inference
        results = self.model(frame, conf=self.confidence, classes=self.classes, verbose=False)[0]
        
        # Convert to supervision detections
        detections = sv.Detections.from_ultralytics(results)
        return detections
