from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('admin-chat/', views.admin_chat_list, name='admin_chat'),
    path('admin-chat/api/rooms/', views.admin_chat_rooms_api, name='admin_chat_rooms_api'),
]
