from django.urls import path
from assistant import views

app_name = 'assistant'

urlpatterns = [
    path('', views.assistant_chat_view, name='index'),
    path('api/query/', views.assistant_query_api, name='api_query'),
]
