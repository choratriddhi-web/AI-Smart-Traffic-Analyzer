from django.urls import path
from detection import views

app_name = 'detection'

urlpatterns = [
    path('', views.detection_dashboard_view, name='index'),
    path('api/model-status/', views.model_status_api, name='model_status'),
]
