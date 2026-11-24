from django.urls import path
from emergency import views

app_name = 'emergency'

urlpatterns = [
    path('', views.emergency_dashboard_view, name='index'),
    path('trigger/', views.trigger_emergency_view, name='trigger'),
    path('<str:log_id>/clear/', views.clear_emergency_view, name='clear'),
]
