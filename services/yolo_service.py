import os
import cv2
import logging
import numpy as np
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# COCO Vehicle Classes
VEHICLE_CLASS_MAP = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Purple theme BGR colors for visualization
COLOR_PURPLE = (215, 60, 160)       # Deep violet / neon purple
COLOR_CYAN = (235, 206, 0)          # Neon cyan
COLOR_MAGENTA = (200, 50, 220)      # Electric magenta
COLOR_GREEN = (80, 220, 100)        # Bright emerald green
COLOR_RED = (60, 60, 230)           # Warning coral red
COLOR_AMBER = (50, 180, 240)        # Amber warning

CLASS_COLORS = {
    'car': (215, 60, 160),         # Purple
    'motorcycle': (235, 206, 0),   # Cyan
    'bus': (50, 180, 240),         # Amber
    'truck': (100, 100, 240)       # Violet-Red
}

class YOLOVehicleDetector:
    """
    Real YOLOv8 vehicle detection and tracking engine using Ultralytics & OpenCV.
    Detects and tracks cars, motorcycles, buses, and trucks.
    """
    _instance = None

    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'yolov8n.pt')
        self.model_path = model_path
        self.model = None
        self.tracker_type = "bytetrack.yaml"
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            if not os.path.exists(self.model_path):
                logger.warning(f"Model file not found at {self.model_path}, downloading yolov8n.pt...")
                self.model = YOLO('yolov8n.pt')
            else:
                self.model = YOLO(self.model_path)
            logger.info(f"YOLOv8 vehicle detection model loaded successfully from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    @classmethod
    def get_detector(cls):
        if cls._instance is None:
            cls._instance = YOLOVehicleDetector()
        return cls._instance

    def detect_and_track(self, frame, confidence_threshold=0.25, track=True):
        """
        Runs real YOLOv8 inference and ByteTrack object tracking on a video frame.
        Returns a list of structured vehicle detection dictionaries.
        """
        if self.model is None or frame is None:
            return []

        detections = []
        try:
            # Classes: 2=car, 3=motorcycle, 5=bus, 7=truck
            classes_to_filter = list(VEHICLE_CLASS_MAP.keys())

            if track:
                results = self.model.track(
                    source=frame,
                    persist=True,
                    classes=classes_to_filter,
                    conf=confidence_threshold,
                    tracker=self.tracker_type,
                    verbose=False
                )
            else:
                results = self.model.predict(
                    source=frame,
                    classes=classes_to_filter,
                    conf=confidence_threshold,
                    verbose=False
                )

            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes

                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        cls_id = int(box.cls[0].item())
                        class_name = VEHICLE_CLASS_MAP.get(cls_id, 'vehicle')
                        conf = float(box.conf[0].item())

                        xyxy = box.xyxy[0].cpu().numpy().astype(int)
                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)

                        # Tracking ID from ByteTrack
                        track_id = None
                        if box.id is not None:
                            try:
                                track_id = int(box.id[0].item())
                            except Exception:
                                track_id = None

                        if track_id is None:
                            # Use coordinate-grid hash ID to avoid colliding with small sequence ints
                            track_id = int(abs(hash((cx // 30, cy // 30, cls_id))) % 90000) + 10000

                        detections.append({
                            "track_id": track_id,
                            "class_id": cls_id,
                            "class_name": class_name,
                            "confidence": round(conf, 3),
                            "bbox": [x1, y1, x2, y2],
                            "center": (cx, cy),
                            "width": x2 - x1,
                            "height": y2 - y1
                        })

        except Exception as e:
            logger.error(f"Error during YOLO inference: {e}")

        return detections

    def draw_detections(self, frame, detections, counting_line=None, lanes=None):
        """
        Draws high-tech purple-themed bounding boxes, tracking badges,
        counting line, and lane demarcations onto the frame.
        """
        if frame is None:
            return None

        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Lanes if provided
        if lanes:
            for lane in lanes:
                pts = lane.get('polygon')
                lane_name = lane.get('name', 'Lane')
                if pts and len(pts) >= 3:
                    pts_np = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated, [pts_np], isClosed=True, color=(160, 50, 190), thickness=2)
                    # Semi-transparent overlay
                    overlay = annotated.copy()
                    cv2.fillPoly(overlay, [pts_np], color=(140, 40, 170))
                    cv2.addWeighted(overlay, 0.15, annotated, 0.85, 0, annotated)

        # 2. Draw Counting Line if provided
        if counting_line:
            p1 = counting_line.get('start', (0, int(h * 0.60)))
            p2 = counting_line.get('end', (w, int(h * 0.60)))
            cv2.line(annotated, p1, p2, COLOR_CYAN, 3)
            # Glowing double-line
            cv2.line(annotated, (p1[0], p1[1] + 2), (p2[0], p2[1] + 2), COLOR_MAGENTA, 1)
            line_count = counting_line.get('count')
            count_label = f"VIRTUAL COUNTING LINE | COUNT: {line_count}" if line_count is not None else "VIRTUAL COUNTING LINE"
            cv2.putText(annotated, count_label, (20, p1[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_CYAN, 2)

        # 3. Draw Bounding Boxes and Labels
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_name = det['class_name']
            track_id = det['track_id']
            conf = det['confidence']
            color = CLASS_COLORS.get(cls_name, COLOR_PURPLE)

            # Sleek bounding box with corner highlights
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Futuristic corner brackets
            corner_len = min(15, int((x2 - x1) / 4))
            # Top-left
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 2)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 2)
            # Top-right
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), (255, 255, 255), 2)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), (255, 255, 255), 2)
            # Bottom-left
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), (255, 255, 255), 2)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), (255, 255, 255), 2)
            # Bottom-right
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 2)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 2)

            # Center point
            cx, cy = det['center']
            cv2.circle(annotated, (cx, cy), 4, COLOR_CYAN, -1)

            # Label text
            label_text = f"#{track_id} {cls_name.upper()} {int(conf * 100)}%"
            (txt_w, txt_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)

            # Label badge background
            badge_y1 = max(0, y1 - txt_h - 8)
            badge_y2 = y1
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + txt_w + 10, badge_y2), (40, 10, 60), -1)
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + txt_w + 10, badge_y2), color, 1)
            cv2.putText(annotated, label_text, (x1 + 5, badge_y2 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        return annotated
