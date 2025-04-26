from django.urls import path
from konnekt import views

urlpatterns = [
    path('', views.index_view, name='chats'),
    path('my_profile/', views.my_profile_view, name='my_profile'),
    path('user/', views.user_profile_view, name='user_profile'),
]
