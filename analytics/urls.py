from django.urls import path
from analytics import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard_view, name='index'),
    path('api/data/', views.analytics_data_api, name='api_data'),
]
