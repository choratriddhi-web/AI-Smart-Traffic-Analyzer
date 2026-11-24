from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from services.mongodb import get_collection
from services.traffic_service import TrafficAnalyzerService
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def density_analysis_view(request):
    """
    Renders Traffic Density Analysis Dashboard (Phase 8).
    Shows camera-wise density categories (LOW, MODERATE, HIGH, VERY HIGH),
    threshold configurations, and recent density event logs.
    """
    density_col = get_collection("density_history")
    recent_history = list(density_col.find().sort("timestamp", -1).limit(20))
    for r in recent_history:
        r['id'] = str(r['_id'])

    traffic_svc = TrafficAnalyzerService.get_service()
    cameras = ["CAM-01", "CAM-02", "CAM-03", "CAM-04"]
    camera_densities = []

    for cid in cameras:
        tracker = traffic_svc._get_tracker_state(cid)
        active_cnt = len(tracker["positions"])
        cat, color = traffic_svc.calculate_density(active_cnt)
        camera_densities.append({
            "camera_id": cid,
            "active_count": active_cnt,
            "density_category": cat,
            "density_color": color,
            "counted_total": tracker["last_counts"]["total"]
        })

    thresholds = {
        "low_max": 5,
        "moderate_max": 12,
        "high_max": 22,
        "very_high_min": 23
    }

    return render(request, 'traffic/density.html', {
        'camera_densities': camera_densities,
        'recent_history': recent_history,
        'thresholds': thresholds
    })

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def lane_management_view(request):
    """
    Renders Lane Management Page (Phase 7).
    Allows authorities to configure, add, edit, and delete traffic lanes.
    """
    lanes_col = get_collection("lanes")
    lanes = list(lanes_col.find().sort([("camera_id", 1), ("lane_number", 1)]))
    for l in lanes:
        l['id'] = str(l['_id'])

    return render(request, 'lanes/index.html', {'lanes': lanes})

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def add_lane_view(request):
    """
    Adds a new lane configuration.
    """
    if request.method == 'POST':
        camera_id = request.POST.get('camera_id', 'CAM-01')
        lane_number = int(request.POST.get('lane_number', 1))
        name = request.POST.get('name', f"Lane {lane_number}")
        direction = request.POST.get('direction', 'Northbound')
        capacity = int(request.POST.get('capacity', 15))

        lanes_col = get_collection("lanes")
        lanes_col.insert_one({
            "camera_id": camera_id,
            "lane_number": lane_number,
            "name": name,
            "direction": direction,
            "capacity": capacity,
            "created_at": datetime.utcnow()
        })
        messages.success(request, f"New lane '{name}' added successfully to {camera_id}.")
        return redirect('traffic:lanes')

    return redirect('traffic:lanes')

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def delete_lane_view(request, lane_id):
    """
    Deletes an existing lane configuration.
    """
    lanes_col = get_collection("lanes")
    lanes_col.delete_one({"_id": ObjectId(lane_id)})
    messages.success(request, "Lane configuration removed successfully.")
    return redirect('traffic:lanes')
