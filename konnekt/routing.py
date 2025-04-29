from django.urls import path
from konnekt import consumers

ws_pattern = [
    path('ws/konnekt/<str:conv_id>/', consumers.ChatConsumer.as_asgi()),
]

