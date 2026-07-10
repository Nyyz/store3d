from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/customer/$', consumers.CustomerChatConsumer.as_asgi()),
    re_path(r'ws/chat/admin/(?P<room_id>\d+)/$', consumers.AdminChatConsumer.as_asgi()),
]
