from django.urls import re_path
from konnekt import consumers


ws_pattern = [
    re_path(r'^ws/konnekt/(?P<conv_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/konnekt/recent-chats/(?P<user_id>[^/]+)/$', consumers.RecentChatsConsumer.as_asgi()),
]

