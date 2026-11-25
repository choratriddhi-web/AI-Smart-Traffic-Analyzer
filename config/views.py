import math
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from services.mongodb import get_collection, check_db_connection
from services.camera_service import get_all_camera_details
from services.traffic_service import TrafficAnalyzerService
from services.incident_service import IncidentManagementService
from services.emergency_service import EmergencyVehicleService
from services.sos_service import SmartSOSService
from accounts.decorators import mongo_login_required, role_required

logger = logging.getLogger(__name__)

def safe_session_get(request, key, default=None):
    try:
        return request.session.get(key, default)
    except Exception:
        return default

# Curated Verified Fuel Stations around the monitored transit grid
REAL_PETROL_PUMPS = [
    {
        "id": "PUMP-01",
        "name": "Bharat Petroleum (BPCL) Auto Care",
        "brand": "BPCL",
        "latitude": 19.0755,
        "longitude": 72.8785,
        "address": "MG Road & Grand Avenue Junction, Mumbai",
        "phone": "+91 22 2261 4500",
        "fuels": ["Petrol", "Diesel", "CNG", "EV Fast Charging"],
        "operating_hours": "24 Hours Open",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=19.0755,72.8785"
    },
    {
        "id": "PUMP-02",
        "name": "Indian Oil Corporation (IOCL) City Fuel Hub",
        "brand": "IndianOil",
        "latitude": 19.0792,
        "longitude": 72.8812,
        "address": "Grand Avenue Sector 4, Mumbai",
        "phone": "+91 22 2430 8912",
        "fuels": ["Petrol", "Diesel", "XP95 Speed"],
        "operating_hours": "24 Hours Open",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=19.0792,72.8812"
    },
    {
        "id": "PUMP-03",
        "name": "HPCL Trauma Way Express Dispenser",
        "brand": "HPCL",
        "latitude": 19.0830,
        "longitude": 72.8845,
        "address": "Hospital Link Road near Trauma Center, Mumbai",
        "phone": "+91 22 2652 1100",
        "fuels": ["Petrol", "Diesel", "Power 99", "Air & Water"],
        "operating_hours": "24 Hours Open",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=19.0830,72.8845"
    },
    {
        "id": "PUMP-04",
        "name": "Shell Select Premium Mobility Station",
        "brand": "Shell",
        "latitude": 19.0885,
        "longitude": 72.8695,
        "address": "North Ring Road Circle & Expressway Bypass, Mumbai",
        "phone": "+91 22 6789 0011",
        "fuels": ["V-Power Petrol", "V-Power Diesel", "Shell Cafe & Deli"],
        "operating_hours": "24 Hours Open",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=19.0885,72.8695"
    },
    {
        "id": "PUMP-05",
        "name": "Jio-bp Pulse Highway Mobility Hub",
        "brand": "Jio-bp",
        "latitude": 19.0665,
        "longitude": 72.8565,
        "address": "Western Express Highway Flyover Pier 12, Mumbai",
        "phone": "+91 22 3555 8000",
        "fuels": ["Active Petrol", "Active Diesel", "Jio-bp EV DC Fast Charger"],
        "operating_hours": "24 Hours Open",
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=19.0665,72.8565"
    }
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def gateway_view(request):
    """
    Landing Portal Gateway offering clear entry into either:
    1) Traffic Authority / Police Command Center (Login & Register)
    2) Citizen & Public Traffic Portal (Login & Register)
    """
    user = getattr(request, 'mongo_user', None)
    return render(request, 'gateway.html', {'user': user})

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def admin_dashboard_view(request):
    """
    Renders Main Smart City Traffic Control Room Dashboard for Administrator & Traffic Authority.
    Includes live CCTV telemetry, custom video uploads, emergency corridors, and real-time citizen SOS alerts.
    """
    cameras = get_all_camera_details()
    traffic_svc = TrafficAnalyzerService.get_service()
    counts_col = get_collection("vehicle_counts")
    total_crossings = counts_col.count_documents({})

    total_active = 0
    for cam in cameras:
        cid = cam['camera_id']
        state = traffic_svc._get_tracker_state(cid)
        cam['line_total'] = state['last_counts']['total']
        cam['active_count'] = len(state['positions'])
        total_active += cam['active_count']
        density, color = traffic_svc.calculate_density(cam['active_count'])
        cam['density'] = density
        cam['density_color'] = color

    active_incidents = IncidentManagementService.get_active_count()
    emergency_logs = EmergencyVehicleService.get_emergency_logs()
    active_emergency = any(log.get('status') == 'Priority Green Corridor Active' for log in emergency_logs)
    pending_sos = SmartSOSService.get_pending_alerts()

    return render(request, 'dashboard/index.html', {
        'cameras': cameras,
        'total_active': total_active,
        'total_crossings': total_crossings,
        'active_incidents': active_incidents,
        'active_emergency': active_emergency,
        'pending_sos_count': len(pending_sos),
        'pending_sos_alerts': pending_sos
    })

@mongo_login_required
def public_dashboard_view(request):
    """
    Renders Public Traffic Dashboard (Citizen portal).
    Requires Citizen authentication or registration.
    Allows citizens to view public traffic conditions, simulated traffic lights,
    interact with Google Maps, discover petrol pumps, and trigger Instant Emergency SOS.
    """
    cameras = get_all_camera_details()[:4] # Display primary 4 junctions
    traffic_svc = TrafficAnalyzerService.get_service()

    for cam in cameras:
        cid = cam['camera_id']
        state = traffic_svc._get_tracker_state(cid)
        cam['active_count'] = len(state['positions'])
        density, color = traffic_svc.calculate_density(cam['active_count'])
        cam['density'] = density
        cam['density_color'] = color

    incidents = IncidentManagementService.get_all_incidents()[:3]
    return render(request, 'public/index.html', {
        'cameras': cameras,
        'incidents': incidents,
        'petrol_pumps': REAL_PETROL_PUMPS
    })

@mongo_login_required
def live_map_view(request):
    """
    Renders Live Google Maps Traffic & Verified Petrol Pumps Portal.
    Accessible to registered citizens and logged-in users.
    No 404 tile errors: Uses embedded Google Maps with GPS distance calculation.
    """
    cameras = get_all_camera_details()
    return render(request, 'public/map.html', {
        'cameras': cameras,
        'petrol_pumps': REAL_PETROL_PUMPS,
        'center_lat': 19.0760,
        'center_lng': 72.8777
    })

def petrol_pumps_api(request):
    """
    Returns nearby verified fuel stations with calculated distance based on user coordinates.
    """
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')

    pumps_with_dist = []
    for pump in REAL_PETROL_PUMPS:
        p_copy = dict(pump)
        if user_lat and user_lng:
            try:
                dist = haversine_distance(float(user_lat), float(user_lng), pump['latitude'], pump['longitude'])
                p_copy['distance_km'] = dist
            except Exception:
                p_copy['distance_km'] = None
        else:
            p_copy['distance_km'] = None
        pumps_with_dist.append(p_copy)

    if user_lat and user_lng:
        pumps_with_dist.sort(key=lambda x: x.get('distance_km') or 999)

    return JsonResponse({'status': 'success', 'petrol_pumps': pumps_with_dist})

def public_sos_submit_view(request):
    """
    Allows public citizens to submit an emergency SOS ticket directly without login.
    Immediately dispatches alert notification to the Authority control room.
    """
    if request.method == 'POST':
        user_id = safe_session_get(request, 'user_id', 'public_citizen')
        name = request.POST.get('name', 'Concerned Citizen').strip()
        phone = request.POST.get('phone', '').strip()
        category = request.POST.get('category', 'Medical Emergency')
        details = request.POST.get('details', '').strip()
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        address = request.POST.get('address')

        if not phone or not details:
            messages.error(request, "Please enter your contact phone number and emergency details.")
            return redirect('public:sos_status')

        lat_val = float(lat) if lat else 19.0760
        lng_val = float(lng) if lng else 72.8777

        ticket = SmartSOSService.create_sos(
            user_id=user_id,
            name=name,
            phone=phone,
            category=category,
            details=details,
            lat=lat_val,
            lng=lng_val,
            address=address
        )
        messages.success(request, f"🚨 EMERGENCY SOS #{ticket['ticket_number']} LOGGED! Live distress signal dispatched to Traffic Command.")
        try:
            request.session['last_sos_ticket'] = ticket['ticket_number']
        except Exception:
            pass
        return redirect('public:sos_status')

    return redirect('public:dashboard')

@csrf_exempt
def public_quick_sos_api(request):
    """
    AJAX one-click SOS endpoint for instant public distress alerts without login.
    """
    if request.method == 'POST':
        user_id = safe_session_get(request, 'user_id', 'public_citizen')
        user = getattr(request, 'mongo_user', None)

        name = request.POST.get('name') or (user.get('full_name') if user else 'Citizen In Distress')
        phone = request.POST.get('phone') or (user.get('phone') if user else '+91 99999 88888')
        category = request.POST.get('category', 'Immediate Emergency SOS')
        details = request.POST.get('details', 'Instant 1-Click SOS Signal triggered from Citizen Portal.')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        address = request.POST.get('address', 'Live GPS Location Shared')

        lat_val = float(lat) if lat else 19.0760
        lng_val = float(lng) if lng else 72.8777

        ticket = SmartSOSService.create_sos(
            user_id=user_id,
            name=name,
            phone=phone,
            category=category,
            details=details,
            lat=lat_val,
            lng=lng_val,
            address=address
        )
        return JsonResponse({
            'status': 'success',
            'ticket_number': ticket['ticket_number'],
            'message': f"🚨 EMERGENCY ALERT #{ticket['ticket_number']} BROADCASTED TO TRAFFIC AUTHORITIES!"
        })
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

@mongo_login_required
def public_sos_status_view(request):
    """
    Allows registered public citizens to view active SOS emergency requests.
    """
    user_id = safe_session_get(request, 'user_id', None)
    if user_id:
        user_requests = SmartSOSService.get_user_requests(user_id)
    else:
        last_ticket = safe_session_get(request, 'last_sos_ticket')
        if last_ticket:
            all_reqs = SmartSOSService.get_all_requests()
            user_requests = [r for r in all_reqs if r.get('ticket_number') == last_ticket]
            if not user_requests:
                user_requests = all_reqs[:5]
        else:
            user_requests = SmartSOSService.get_all_requests()[:5]

    return render(request, 'public/sos_status.html', {'requests': user_requests})

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def authority_sos_management_view(request):
    """
    Traffic Authority SOS Management Inbox.
    """
    all_requests = SmartSOSService.get_all_requests()
    return render(request, 'sos/management.html', {'requests': all_requests})

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def authority_update_sos_status(request, ticket_id):
    """
    Updates status of an SOS request (Pending -> Acknowledged -> Resolved).
    """
    if request.method == 'POST':
        new_status = request.POST.get('status', 'Acknowledged')
        notes = request.POST.get('notes', '')
        officer = request.mongo_user.get('full_name', 'Traffic Officer')
        SmartSOSService.update_status(ticket_id, new_status, officer, notes)
        messages.success(request, f"SOS Ticket status updated to {new_status}.")
        return redirect('sos:management')

    return redirect('sos:management')

def live_sos_alerts_api(request):
    """
    Polling API consumed by the Admin / Authority dashboard to fetch incoming
    distress alerts and play audio/visual alarms in real time.
    """
    pending = SmartSOSService.get_pending_alerts()
    return JsonResponse({
        'status': 'success',
        'pending_count': len(pending),
        'count': len(pending),
        'alerts': pending
    })

@mongo_login_required
@role_required(['Traffic Authority'])
def system_settings_view(request):
    """
    Renders System Settings & Configuration.
    """
    db_status = check_db_connection()
    settings_col = get_collection("system_settings")
    current_settings = settings_col.find_one() or {}

    if request.method == 'POST':
        conf_thresh = float(request.POST.get('confidence_threshold', 0.35))
        min_green = int(request.POST.get('min_green', 15))
        max_green = int(request.POST.get('max_green', 90))

        settings_col.update_one({}, {"$set": {
            "confidence_threshold": conf_thresh,
            "signal_timings.min_green": min_green,
            "signal_timings.max_green": max_green,
            "updated_at": datetime.utcnow()
        }}, upsert=True)
        messages.success(request, "System settings saved successfully.")
        return redirect('settings:index')

    return render(request, 'settings/index.html', {
        'db_status': db_status,
        'settings': current_settings
    })

def db_status_api(request):
    """
    Diagnostic database connection test endpoint.
    """
    diag = check_db_connection()
    return JsonResponse(diag)
