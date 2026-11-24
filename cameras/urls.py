from django.urls import path
from cameras import views

app_name = 'cameras'

urlpatterns = [
    path('', views.camera_list_view, name='list'),
    path('upload/', views.upload_custom_video_view, name='upload'),
    path('<str:camera_id>/', views.camera_detail_view, name='detail'),
    path('<str:camera_id>/upload-video/', views.update_specific_camera_video_view, name='update_video'),
    path('<str:camera_id>/delete/', views.delete_camera_view, name='delete'),
    path('<str:camera_id>/stream/', views.camera_stream_view, name='stream'),
    path('<str:camera_id>/video/', views.camera_video_file_view, name='video_file'),
    path('<str:camera_id>/api/stats/', views.camera_stats_api, name='api_stats'),
]
