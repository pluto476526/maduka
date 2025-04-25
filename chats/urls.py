from django.urls import path
from chats import views

urlpatterns = [
    path('', views.index_view, name='chats'),
    path('my_profile/', views.my_profile_view, name='my_profile'),
]
