from django.shortcuts import render, redirect
from django.contrib import messages
from services.emergency_service import EmergencyVehicleService
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def emergency_dashboard_view(request):
    """
    Renders Emergency Vehicle Monitoring Interface (Phase 13).
    Displays model status (honest 'NOT CONFIGURED' for standard weights),
    plus dedicated Academic Demonstration Mode for Green Wave priority corridors.
    """
    model_status = EmergencyVehicleService.get_model_status()
    logs = EmergencyVehicleService.get_emergency_logs()

    return render(request, 'emergency/index.html', {
        'model_status': model_status,
        'emergency_logs': logs,
        'cameras': ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04']
    })

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def trigger_emergency_view(request):
    """
    Activates an academic demonstration green corridor for emergency responder vehicles.
    """
    if request.method == 'POST':
        camera_id = request.POST.get('camera_id', 'CAM-02')
        v_type = request.POST.get('vehicle_type', 'Ambulance')

        EmergencyVehicleService.trigger_emergency_simulation(
            camera_id=camera_id,
            vehicle_type=v_type,
            priority_action="GREEN_CORRIDOR_ACTIVATE"
        )
        messages.warning(request, f"Emergency Green Corridor activated on {camera_id} for {v_type}!")
        return redirect('emergency:index')

    return redirect('emergency:index')

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def clear_emergency_view(request, log_id):
    """
    Clears active priority green corridor status.
    """
    EmergencyVehicleService.clear_priority(log_id)
    messages.info(request, "Emergency transit complete. Corridor returned to normal adaptive cycle.")
    return redirect('emergency:index')
