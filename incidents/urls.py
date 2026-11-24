from django.urls import path
from incidents import views

app_name = 'incidents'

urlpatterns = [
    path('', views.incidents_dashboard_view, name='index'),
    path('generate/', views.generate_incident_view, name='generate'),
    path('<str:incident_id>/acknowledge/', views.acknowledge_incident_view, name='acknowledge'),
    path('<str:incident_id>/resolve/', views.resolve_incident_view, name='resolve'),
]
