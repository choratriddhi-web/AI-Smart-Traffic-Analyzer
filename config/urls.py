from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.shortcuts import redirect
from config import views
from accounts import views as accounts_views

def root_redirect(request):
    user = getattr(request, 'mongo_user', None)
    if user and user.get('role') == 'Traffic Authority':
        return redirect('dashboard:index')
    elif user and user.get('role') == 'Public User':
        return redirect('public:dashboard')
    return views.gateway_view(request)

# Properly namespaced URL patterns
dashboard_patterns = ([
    path('', views.admin_dashboard_view, name='index'),
], 'dashboard')

public_patterns = ([
    path('', views.public_dashboard_view, name='dashboard'),
    path('login/', accounts_views.citizen_login_view, name='login'),
    path('register/', accounts_views.citizen_register_view, name='register'),
    path('map/', views.live_map_view, name='map'),
    path('sos/submit/', views.public_sos_submit_view, name='sos_submit'),
    path('sos/quick/', views.public_quick_sos_api, name='sos_quick'),
    path('sos/status/', views.public_sos_status_view, name='sos_status'),
], 'public')

sos_patterns = ([
    path('management/', views.authority_sos_management_view, name='management'),
    path('<str:ticket_id>/update/', views.authority_update_sos_status, name='update'),
    path('api/live-alerts/', views.live_sos_alerts_api, name='live_alerts'),
], 'sos')

settings_patterns = ([
    path('', views.system_settings_view, name='index'),
], 'settings')

urlpatterns = [
    # Root, Gateway & Diagnostic routes
    path('', root_redirect, name='root'),
    path('gateway/', views.gateway_view, name='gateway'),
    path('api/health/db/', views.db_status_api, name='api_db_health'),
    path('api/petrol-pumps/', views.petrol_pumps_api, name='api_petrol_pumps'),

    # Namespaced Sub-Systems
    path('dashboard/', include(dashboard_patterns, namespace='dashboard')),
    path('public/', include(public_patterns, namespace='public')),
    path('sos/', include(sos_patterns, namespace='sos')),
    path('settings/', include(settings_patterns, namespace='settings')),

    # Feature Apps
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('cameras/', include('cameras.urls', namespace='cameras')),
    path('detection/', include('detection.urls', namespace='detection')),
    path('traffic/', include('traffic.urls', namespace='traffic')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('prediction/', include('prediction.urls', namespace='prediction')),
    path('signals/', include('signals.urls', namespace='signals')),
    path('incidents/', include('incidents.urls', namespace='incidents')),
    path('emergency/', include('emergency.urls', namespace='emergency')),
    path('assistant/', include('assistant.urls', namespace='assistant')),
]

# Always serve media files (Camera MP4 videos, snapshots, uploads) and static files in both dev and production
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'static'}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
