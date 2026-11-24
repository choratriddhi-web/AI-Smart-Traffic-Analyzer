from django.urls import path
from traffic import views

app_name = 'traffic'

urlpatterns = [
    path('density/', views.density_analysis_view, name='density'),
    path('lanes/', views.lane_management_view, name='lanes'),
    path('lanes/add/', views.add_lane_view, name='add_lane'),
    path('lanes/<str:lane_id>/delete/', views.delete_lane_view, name='delete_lane'),
]
