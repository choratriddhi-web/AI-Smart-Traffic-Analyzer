from django.shortcuts import render
from django.http import JsonResponse
from services.prediction_service import TrafficPredictionService
from accounts.decorators import mongo_login_required, role_required

@mongo_login_required
@role_required(['Administrator', 'Traffic Authority', 'Public User'])
def prediction_dashboard_view(request):
    """
    Renders Machine Learning Traffic Prediction Interface (Phase 10).
    Accessible to Traffic Authorities and Public Citizens.
    """
    camera_id = request.GET.get('camera_id', 'CAM-01')
    pred_data = TrafficPredictionService.predict_traffic(camera_id)
    return render(request, 'prediction/index.html', {
        'prediction': pred_data,
        'selected_camera': camera_id,
        'cameras': ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-04']
    })

def prediction_api(request, camera_id):
    """
    Returns JSON predictions for +5, +15, +30 minutes based on Linear Regression.
    """
    data = TrafficPredictionService.predict_traffic(camera_id)
    return JsonResponse(data)
