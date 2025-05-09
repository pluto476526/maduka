from django.urls import path
from konnekt import views

urlpatterns = [
    path('', views.index_view, name='chats'),
    path('profile/', views.my_profile_view, name='my_profile'),
    path('profile/<str:identifier>/', views.user_profile_view, name='user_profile'),
    path('upload_attachment/', views.upload_attachment, name='upload_attachment'),
    path('get_user_func/', views.get_user_func, name='get_user'),
    path('notifications/subscribe/', views.save_subscription, name='save_subscription'),
    path('notifications/vapid-public-key/', views.get_vapid_public_key, name='get_vapid_key'),
    path('<str:convo_id>/', views.chat_view, name='chat_view'),
]
