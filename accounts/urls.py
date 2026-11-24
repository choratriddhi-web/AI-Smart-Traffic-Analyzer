from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('citizen/login/', views.citizen_login_view, name='citizen_login'),
    path('citizen/register/', views.citizen_register_view, name='citizen_register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_management_view, name='users'),
    path('users/<str:user_id>/update/', views.update_user_role, name='user_update'),
]
