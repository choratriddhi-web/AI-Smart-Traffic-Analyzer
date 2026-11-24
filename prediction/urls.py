from django.urls import path
from prediction import views

app_name = 'prediction'

urlpatterns = [
    path('', views.prediction_dashboard_view, name='index'),
    path('api/<str:camera_id>/', views.prediction_api, name='api_predict'),
]
