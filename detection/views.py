import os
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from services.yolo_service import YOLOVehicleDetector, VEHICLE_CLASS_MAP
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def detection_dashboard_view(request):
    """
    Renders the Vehicle Detection AI Control Center.
    Displays model status, supported classes, confidence thresholds, and test controls.
    """
    detector = YOLOVehicleDetector.get_detector()
    model_loaded = detector.model is not None

    model_info = {
        "model_loaded": model_loaded,
        "model_name": "YOLOv8 Nano (Ultralytics)",
        "weights_file": "ai_models/yolov8n.pt",
        "file_exists": os.path.exists(os.path.join(settings.BASE_DIR, 'ai_models', 'yolov8n.pt')),
        "tracker": "ByteTrack (persist=True)",
        "classes": list(VEHICLE_CLASS_MAP.values()),
        "confidence_threshold": 0.35,
        "input_resolution": "640x640 auto-stride",
        "backend_framework": "PyTorch + OpenCV"
    }

    return render(request, 'detection/index.html', {'model_info': model_info})

def model_status_api(request):
    """
    Returns AI model health and configuration status.
    """
    detector = YOLOVehicleDetector.get_detector()
    return JsonResponse({
        "status": "ready" if detector.model is not None else "error",
        "weights": "yolov8n.pt",
        "classes": VEHICLE_CLASS_MAP,
        "tracker": detector.tracker_type
    })
