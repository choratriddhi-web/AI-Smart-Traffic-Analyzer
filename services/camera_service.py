import os
import cv2
import time
import logging
import threading
from pathlib import Path
from django.conf import settings
from services.mongodb import get_collection

logger = logging.getLogger(__name__)

class CameraStreamManager:
    """
    Manages video capture streams for simulated CCTV cameras and custom uploaded videos.
    Ensures safe resource recycling, continuous looping, and thread safety.
    """
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, camera_id: str, video_path: str):
        self.camera_id = camera_id
        self.video_path = video_path
        self.cap = None
        self.current_frame = None
        self.frame_count = 0
        self.fps = 25
        self.is_running = False
        self.lock = threading.Lock()
        self.last_read_time = 0
        self.has_looped = False
        self._init_capture()

    def _init_capture(self):
        with self.lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
            if os.path.exists(self.video_path):
                self.cap = cv2.VideoCapture(self.video_path)
                if self.cap.isOpened():
                    self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
                    self.is_running = True
                    logger.info(f"Initialized video capture for {self.camera_id}: {self.video_path} (FPS: {self.fps})")
                else:
                    logger.error(f"Could not open video file: {self.video_path}")
                    self.is_running = False
            else:
                logger.warning(f"Video file not found at: {self.video_path}")
                self.is_running = False

    def get_frame(self):
        """
        Reads next frame from video file, looping seamlessly to the start when reaching EOF.
        """
        with self.lock:
            if not self.is_running or self.cap is None or not self.cap.isOpened():
                self._init_capture()
                if not self.is_running:
                    return None

            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Loop video to beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.has_looped = True
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    return None

            self.frame_count += 1
            self.current_frame = frame
            self.last_read_time = time.time()
            return frame

    def release(self):
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.is_running = False

    @classmethod
    def reset_camera(cls, camera_id: str):
        """Releases and removes camera manager instance so it reloads with fresh video."""
        with cls._lock:
            if camera_id in cls._instances:
                cls._instances[camera_id].release()
                del cls._instances[camera_id]

    @classmethod
    def get_manager(cls, camera_id: str):
        with cls._lock:
            if camera_id not in cls._instances:
                # Look up camera record from DB
                cameras_col = get_collection('cameras')
                cam_data = cameras_col.find_one({"camera_id": camera_id})

                if cam_data and cam_data.get('video_file'):
                    video_file = cam_data['video_file']
                else:
                    video_file = f"{camera_id.lower()}.mp4"

                # Check candidate paths in media/cameras/ and static/cameras/
                fallback_map = {
                    "CAM-01": "01_busy_city_intersection.mp4",
                    "CAM-02": "02_ambulance_emergency.mp4",
                    "CAM-03": "03_roundabout.mp4",
                    "CAM-04": "04_accident_detection.mp4"
                }
                fallback_name = fallback_map.get(camera_id, video_file)

                candidates = [
                    os.path.join(settings.BASE_DIR, 'media', 'cameras', video_file),
                    os.path.join(settings.BASE_DIR, 'media', 'cameras', fallback_name),
                    os.path.join(settings.BASE_DIR, 'static', 'cameras', video_file),
                    os.path.join(settings.BASE_DIR, 'static', 'cameras', fallback_name),
                ]
                media_video_path = candidates[0]
                for p in candidates:
                    if os.path.exists(p):
                        media_video_path = p
                        break

                cls._instances[camera_id] = CameraStreamManager(camera_id, media_video_path)
            return cls._instances[camera_id]

def get_all_camera_details():
    """
    Returns live metadata, status, and configuration for all registered cameras.
    """
    cameras_col = get_collection('cameras')
    cameras = list(cameras_col.find().sort("camera_id", 1))
    results = []

    for cam in cameras:
        cam_id = cam.get('camera_id')
        video_filename = cam.get('video_file', '')
        video_full_path = os.path.join(settings.BASE_DIR, 'media', 'cameras', video_filename)
        exists = os.path.exists(video_full_path)
        if not exists:
            fallback_map = {
                "CAM-01": "01_busy_city_intersection.mp4",
                "CAM-02": "02_ambulance_emergency.mp4",
                "CAM-03": "03_roundabout.mp4",
                "CAM-04": "04_accident_detection.mp4"
            }
            fb = fallback_map.get(cam_id, '')
            if fb and os.path.exists(os.path.join(settings.BASE_DIR, 'media', 'cameras', fb)):
                video_filename = fb
                exists = True

        results.append({
            "camera_id": cam_id,
            "name": cam.get('name', f"Camera {cam_id}"),
            "location": cam.get('location', 'Urban Traffic Grid'),
            "latitude": cam.get('latitude', 19.0760),
            "longitude": cam.get('longitude', 72.8777),
            "video_file": video_filename,
            "video_url": f"/media/cameras/{video_filename}",
            "file_exists": exists,
            "status": "Active" if exists else "Video Missing",
            "fps": cam.get('fps', 25),
            "resolution": cam.get('resolution', '1280x720'),
            "description": cam.get('description', ''),
            "is_custom_upload": cam.get('is_custom_upload', False)
        })
    return results

def get_camera_info(camera_id: str):
    """Returns single camera metadata."""
    cameras_col = get_collection('cameras')
    cam = cameras_col.find_one({"camera_id": camera_id})
    if not cam:
        return None
    cam['id'] = str(cam['_id'])
    video_filename = cam.get('video_file', '')
    video_full_path = os.path.join(settings.BASE_DIR, 'media', 'cameras', video_filename)
    exists = os.path.exists(video_full_path)
    if not exists:
        fallback_map = {
            "CAM-01": "01_busy_city_intersection.mp4",
            "CAM-02": "02_ambulance_emergency.mp4",
            "CAM-03": "03_roundabout.mp4",
            "CAM-04": "04_accident_detection.mp4"
        }
        fb = fallback_map.get(camera_id, '')
        if fb and os.path.exists(os.path.join(settings.BASE_DIR, 'media', 'cameras', fb)):
            video_filename = fb
            exists = True
            cam['video_file'] = fb
    cam['video_url'] = f"/media/cameras/{video_filename}"
    cam['file_exists'] = exists
    return cam

def update_camera_video_file(camera_id: str, file_obj):
    """
    Directly uploads and replaces the video file for CAM-01, CAM-02, CAM-03, CAM-04
    or any camera. Automatically probes resolution, updates MongoDB, and resets stream.
    """
    from datetime import datetime
    from services.traffic_service import TrafficAnalyzerService

    media_cameras_dir = os.path.join(settings.BASE_DIR, 'media', 'cameras')
    os.makedirs(media_cameras_dir, exist_ok=True)

    timestamp = int(time.time())
    safe_name = f"{camera_id.lower()}_{timestamp}_{file_obj.name.replace(' ', '_')}"
    full_path = os.path.join(media_cameras_dir, safe_name)

    with open(full_path, 'wb+') as dest:
        for chunk in file_obj.chunks():
            dest.write(chunk)

    # Probe FPS and resolution
    fps = 25
    resolution = "1280x720"
    try:
        cap = cv2.VideoCapture(full_path)
        if cap.isOpened():
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
            resolution = f"{w}x{h}"
            cap.release()
    except Exception as e:
        logger.warning(f"Could not probe uploaded video dimensions: {e}")

    # Update in MongoDB
    cameras_col = get_collection('cameras')
    cameras_col.update_one(
        {"camera_id": camera_id},
        {"$set": {
            "video_file": safe_name,
            "fps": fps,
            "resolution": resolution,
            "status": "Active",
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )

    # Reset in-memory stream manager and tracking counts so it reloads cleanly
    CameraStreamManager.reset_camera(camera_id)
    traffic_svc = TrafficAnalyzerService.get_service()
    if camera_id in traffic_svc.camera_trackers:
        del traffic_svc.camera_trackers[camera_id]

    logger.info(f"Updated video for {camera_id}: {safe_name} ({resolution}, {fps} FPS)")
    return safe_name

def register_custom_video(file_obj, title: str, location: str = "Custom Upload Sector"):
    """
    Saves an uploaded video file, probes its metadata, and registers it as a new
    CCTV analysis camera in MongoDB.
    """
    from datetime import datetime

    upload_dir = os.path.join(settings.BASE_DIR, 'media', 'cameras', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = int(time.time())
    safe_filename = f"{timestamp}_{file_obj.name.replace(' ', '_')}"
    full_path = os.path.join(upload_dir, safe_filename)

    with open(full_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

    fps = 25
    resolution = "1280x720"
    try:
        cap = cv2.VideoCapture(full_path)
        if cap.isOpened():
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
            resolution = f"{w}x{h}"
            cap.release()
    except Exception as e:
        logger.warning(f"Could not probe video dimensions: {e}")

    cameras_col = get_collection('cameras')
    count = cameras_col.count_documents({}) + 1
    camera_id = f"CAM-{count:02d}"

    relative_video_file = f"uploads/{safe_filename}"

    new_cam = {
        "camera_id": camera_id,
        "name": title or f"Custom Video {camera_id}",
        "location": location or "Custom Video Analysis Grid",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "video_file": relative_video_file,
        "status": "Active",
        "fps": fps,
        "resolution": resolution,
        "created_at": datetime.utcnow(),
        "is_custom_upload": True,
        "description": f"Custom uploaded video: {file_obj.name} for vehicle detection and virtual line counting."
    }
    cameras_col.insert_one(new_cam)
    logger.info(f"Custom video registered successfully as {camera_id}: {relative_video_file}")
    return new_cam
