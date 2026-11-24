import logging
from datetime import datetime
from services.mongodb import get_collection

logger = logging.getLogger(__name__)

class TrafficAnalyzerService:
    """
    Handles virtual line counting, lane tracking, and traffic density categorization.
    """
    _instance = None

    def __init__(self):
        # In-memory tracking state: { camera_id: { "counted_ids": set(), "positions": { track_id: (cx, cy) } } }
        self.camera_trackers = {}
        # Cumulative stats: { camera_id: { "total": int, "by_class": { "car": 0, ... } } }
        self.camera_totals = {}

    @classmethod
    def get_service(cls):
        if cls._instance is None:
            cls._instance = TrafficAnalyzerService()
        return cls._instance

    def _get_tracker_state(self, camera_id: str):
        if camera_id not in self.camera_trackers:
            # Query existing count from MongoDB if available
            initial_total = 0
            initial_classes = {"total": 0, "car": 0, "motorcycle": 0, "bus": 0, "truck": 0}
            try:
                counts_col = get_collection("vehicle_counts")
                stored_counts = list(counts_col.find({"camera_id": camera_id}))
                if stored_counts:
                    initial_total = len(stored_counts)
                    initial_classes["total"] = initial_total
                    for sc in stored_counts:
                        vtype = sc.get("vehicle_type", "car")
                        initial_classes[vtype] = initial_classes.get(vtype, 0) + 1
            except Exception:
                pass

            self.camera_trackers[camera_id] = {
                "counted_ids": set(),
                "history": {},      # {tid: {"last_pos": (cx, cy), "last_y2": y2, "unseen": 0}}
                "positions": {},
                "last_counts": initial_classes
            }
        return self.camera_trackers[camera_id]

    def _ccw(self, A, B, C):
        """Tests counter-clockwise orientation of three points."""
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def _intersect(self, A, B, C, D):
        """Returns True if line segment AB intersects line segment CD."""
        return self._ccw(A, C, D) != self._ccw(B, C, D) and self._ccw(A, B, C) != self._ccw(A, B, D)

    def process_frame_tracking(self, camera_id: str, detections: list, frame_w: int, frame_h: int):
        """
        Evaluates virtual line crossings for current detections with multi-frame trajectory
        interpolation to ensure accurate real-world vehicle counting.
        """
        tracker = self._get_tracker_state(camera_id)
        counted_ids = tracker["counted_ids"]
        history = tracker.setdefault("history", {})
        last_counts = tracker["last_counts"]

        # Check if camera manager looped video back to start
        try:
            from services.camera_service import CameraStreamManager
            cam_mgr = CameraStreamManager.get_manager(camera_id)
            if getattr(cam_mgr, 'has_looped', False):
                # Video looped; reset counted_ids for the new loop wave while preserving cumulative totals
                counted_ids.clear()
                history.clear()
                cam_mgr.has_looped = False
        except Exception:
            pass

        # Full-width virtual counting line placed at 60% of frame height
        line_y = int(frame_h * 0.60)
        line_start = (0, line_y)
        line_end = (frame_w, line_y)

        new_crossings = []
        active_tids = set()

        for det in detections:
            tid = det["track_id"]
            curr_pos = det["center"]
            cx, cy = curr_pos
            bbox = det.get("bbox", [0, 0, 0, 0])
            y2 = bbox[3] if len(bbox) >= 4 else cy
            cls_name = det["class_name"]
            active_tids.add(tid)

            # Check if already counted on this cycle
            if tid in counted_ids:
                # Still update position
                if tid in history:
                    history[tid]["last_pos"] = curr_pos
                    history[tid]["last_y2"] = y2
                    history[tid]["unseen"] = 0
                else:
                    history[tid] = {"last_pos": curr_pos, "last_y2": y2, "unseen": 0}
                continue

            # Check for crossing against previous position
            if tid in history:
                old_info = history[tid]
                old_pos = old_info["last_pos"]
                old_y = old_pos[1]
                old_y2 = old_info.get("last_y2", old_y)

                # Detection criteria:
                # 1. Direct segment intersect
                # 2. Center crossing line_y (downward or upward)
                # 3. Leading edge (y2) crossing line_y
                has_intersected = self._intersect(old_pos, curr_pos, line_start, line_end)
                has_crossed_cy = (old_y < line_y <= cy) or (old_y > line_y >= cy)
                has_crossed_y2 = (old_y2 < line_y <= y2) or (old_y2 > line_y >= y2)
                in_band = (abs(cy - line_y) <= 15 and abs(cy - old_y) >= 4)

                if has_intersected or has_crossed_cy or has_crossed_y2 or in_band:
                    counted_ids.add(tid)
                    last_counts["total"] += 1
                    last_counts[cls_name] = last_counts.get(cls_name, 0) + 1

                    crossing_event = {
                        "camera_id": camera_id,
                        "track_id": tid,
                        "vehicle_type": cls_name,
                        "confidence": det["confidence"],
                        "timestamp": datetime.utcnow()
                    }
                    new_crossings.append(crossing_event)

                # Update history
                history[tid]["last_pos"] = curr_pos
                history[tid]["last_y2"] = y2
                history[tid]["unseen"] = 0
            else:
                # First time seeing this tid
                history[tid] = {"last_pos": curr_pos, "last_y2": y2, "unseen": 0}

        # Purge stale tracks unseen for more than 45 frames (~1.8 seconds)
        for tid in list(history.keys()):
            if tid not in active_tids:
                history[tid]["unseen"] += 1
                if history[tid]["unseen"] > 45:
                    del history[tid]

        tracker["positions"] = {tid: history[tid]["last_pos"] for tid in active_tids if tid in history}

        # Save new crossings to MongoDB if any
        if new_crossings:
            try:
                counts_col = get_collection("vehicle_counts")
                counts_col.insert_many(new_crossings)
            except Exception as e:
                logger.warning(f"Could not persist vehicle crossings: {e}")

        # Active vehicles in frame right now
        active_in_frame = len(detections)
        active_by_class = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}
        for det in detections:
            c = det["class_name"]
            active_by_class[c] = active_by_class.get(c, 0) + 1

        # Calculate density
        density_cat, density_color = self.calculate_density(active_in_frame)

        # Record density history in DB periodically
        try:
            density_col = get_collection("density_history")
            density_col.insert_one({
                "camera_id": camera_id,
                "active_vehicles": active_in_frame,
                "density_category": density_cat,
                "classes": active_by_class,
                "timestamp": datetime.utcnow()
            })
        except Exception:
            pass

        return {
            "active_count": active_in_frame,
            "active_by_class": active_by_class,
            "line_counted_total": last_counts["total"],
            "line_counted_by_class": last_counts,
            "density_category": density_cat,
            "density_color": density_color,
            "counting_line": {"start": line_start, "end": line_end, "count": last_counts["total"]}
        }

    def calculate_density(self, vehicle_count: int):
        """
        Classifies traffic density into LOW, MODERATE, HIGH, VERY HIGH.
        """
        if vehicle_count <= 5:
            return "LOW", "success"         # Green
        elif vehicle_count <= 12:
            return "MODERATE", "info"      # Cyan/Blue
        elif vehicle_count <= 22:
            return "HIGH", "warning"       # Amber/Orange
        else:
            return "VERY HIGH", "danger"   # Red

    def get_lane_analysis(self, camera_id: str, detections: list, frame_w: int, frame_h: int):
        """
        Divides camera field of view into configured lanes or default vertical lanes.
        Calculates vehicle count, queue length, and density per lane.
        """
        lanes_col = get_collection("lanes")
        db_lanes = list(lanes_col.find({"camera_id": camera_id}).sort("lane_number", 1))

        # Default 3 lanes if none configured in DB
        if not db_lanes:
            lane_w = frame_w // 3
            db_lanes = [
                {"camera_id": camera_id, "lane_number": 1, "name": "Lane 1 - Left", "capacity": 15},
                {"camera_id": camera_id, "lane_number": 2, "name": "Lane 2 - Center", "capacity": 20},
                {"camera_id": camera_id, "lane_number": 3, "name": "Lane 3 - Right", "capacity": 15},
            ]

        num_lanes = len(db_lanes)
        lane_width = frame_w / max(1, num_lanes)

        lane_results = []
        for idx, lane in enumerate(db_lanes):
            lane_num = lane.get("lane_number", idx + 1)
            x_min = idx * lane_width
            x_max = (idx + 1) * lane_width

            # Find detections belonging to this lane
            lane_vehicles = [d for d in detections if x_min <= d["center"][0] < x_max]
            v_count = len(lane_vehicles)

            # Estimate queue length: vehicles stacked in bottom 50% of the frame
            queue_vehicles = [d for d in lane_vehicles if d["center"][1] > frame_h * 0.45]
            queue_len = len(queue_vehicles)

            cap = lane.get("capacity", 15)
            density_pct = min(100, int((v_count / max(1, cap)) * 100))

            if density_pct < 35:
                l_density = "LOW"
            elif density_pct < 70:
                l_density = "MODERATE"
            elif density_pct < 90:
                l_density = "HIGH"
            else:
                l_density = "VERY HIGH"

            lane_results.append({
                "lane_id": str(lane.get("_id", f"lane_{lane_num}")),
                "lane_number": lane_num,
                "name": lane.get("name", f"Lane {lane_num}"),
                "direction": lane.get("direction", "Normal"),
                "vehicle_count": v_count,
                "queue_length": queue_len,
                "density_category": l_density,
                "density_percentage": density_pct,
                "capacity": cap,
                "boundary": [int(x_min), 0, int(x_max), frame_h]
            })

        return lane_results
