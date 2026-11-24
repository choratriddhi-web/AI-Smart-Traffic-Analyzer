from django.shortcuts import render
from django.http import JsonResponse
from services.signal_service import AISignalRecommendationEngine
from services.qlearning_service import QLearningTrafficAgent
from services.traffic_service import TrafficAnalyzerService
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority', 'Public User'])
def signals_dashboard_view(request):
    """
    Renders AI Signal Optimization and Recommendation Interface (Phase 9).
    Accessible to Traffic Authorities and Public Citizens.
    """
    camera_id = request.GET.get('camera_id', 'CAM-01')
    traffic_svc = TrafficAnalyzerService.get_service()
    tracker = traffic_svc._get_tracker_state(camera_id)
    v_count = len(tracker["positions"]) or 14
    density_cat, _ = traffic_svc.calculate_density(v_count)

    rec = AISignalRecommendationEngine.calculate_recommendation(
        camera_id=camera_id,
        vehicle_count=v_count,
        max_queue=max(2, int(v_count * 0.45)),
        density_category=density_cat,
        wait_time_sec=42
    )

    return render(request, 'signals/index.html', {
        'recommendation': rec,
        'selected_camera': camera_id,
        'cameras': ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04']
    })

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority', 'Public User'])
def qlearning_view(request):
    """
    Renders Reinforcement Learning Q-Learning Academic Simulation (Phase 11).
    """
    agent = QLearningTrafficAgent()
    sim_data = agent.run_comparison_simulation(initial_queue=14, initial_density="HIGH", steps=20)
    return render(request, 'signals/qlearning.html', {'sim_data': sim_data})

def signal_recommendation_api(request, camera_id):
    """
    JSON API returning dynamic signal recommendation for a camera.
    """
    v_count = int(request.GET.get('count', 12))
    queue = int(request.GET.get('queue', 4))
    density = request.GET.get('density', 'MODERATE')
    wait_time = int(request.GET.get('wait', 35))

    rec = AISignalRecommendationEngine.calculate_recommendation(
        camera_id=camera_id,
        vehicle_count=v_count,
        max_queue=queue,
        density_category=density,
        wait_time_sec=wait_time
    )
    return JsonResponse(rec)

def qlearning_simulate_api(request):
    """
    JSON API running a new Q-Learning comparison episode on demand.
    """
    q = int(request.GET.get('queue', 14))
    density = request.GET.get('density', 'HIGH')
    steps = int(request.GET.get('steps', 20))

    agent = QLearningTrafficAgent()
    sim = agent.run_comparison_simulation(initial_queue=q, initial_density=density, steps=steps)
    return JsonResponse(sim)
