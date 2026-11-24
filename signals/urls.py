from django.urls import path
from signals import views

app_name = 'signals'

urlpatterns = [
    path('', views.signals_dashboard_view, name='index'),
    path('q-learning/', views.qlearning_view, name='qlearning'),
    path('qlearning/', views.qlearning_view, name='qlearning_alias'),
    path('api/recommend/<str:camera_id>/', views.signal_recommendation_api, name='api_recommend'),
    path('api/q-learning/simulate/', views.qlearning_simulate_api, name='api_qlearning'),
]
