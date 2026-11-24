from django.shortcuts import render, redirect
from django.contrib import messages
from services.incident_service import IncidentManagementService
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def incidents_dashboard_view(request):
    """
    Renders Accident & Incident Monitoring Interface (Phase 12).
    """
    IncidentManagementService.seed_demo_incident_if_empty()
    all_incidents = IncidentManagementService.get_all_incidents()
    active_count = IncidentManagementService.get_active_count()

    return render(request, 'incidents/index.html', {
        'incidents': all_incidents,
        'active_count': active_count,
        'cameras': ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04']
    })

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def generate_incident_view(request):
    """
    Allows generating a demonstration incident to test response workflows.
    """
    if request.method == 'POST':
        camera_id = request.POST.get('camera_id', 'CAM-04')
        category = request.POST.get('category', 'Vehicle Collision / Stoppage')
        location = request.POST.get('location', 'Highway Junction Pier 14')
        description = request.POST.get('description', 'Simulated collision with vehicle lane obstruction.')

        doc = IncidentManagementService.create_incident(
            camera_id=camera_id,
            category=category,
            location=location,
            description=description,
            method="Demonstration Engine (Simulation)"
        )
        messages.warning(request, f"New Incident Alert generated: {doc['incident_id']} on {camera_id}.")
        return redirect('incidents:index')

    return redirect('incidents:index')

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def acknowledge_incident_view(request, incident_id):
    """
    Acknowledges an active incident.
    """
    user_name = request.mongo_user.get('full_name', request.mongo_user.get('username'))
    IncidentManagementService.acknowledge_incident(incident_id, user_name)
    messages.info(request, "Incident acknowledged. Emergency units notified.")
    return redirect('incidents:index')

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority'])
def resolve_incident_view(request, incident_id):
    """
    Resolves an incident with notes.
    """
    notes = request.POST.get('notes', 'Incident cleared by field personnel.')
    IncidentManagementService.resolve_incident(incident_id, notes)
    messages.success(request, "Incident marked as Resolved.")
    return redirect('incidents:index')
