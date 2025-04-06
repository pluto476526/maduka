from django.urls import path
from main import views


urlpatterns = [
    path('shops/', views.all_shops_view, name='main_all_shops'),
    path('profile/<str:shop_name>', views.shop_profile_view, name='main_shop_profile'),
    path('registration/pending/', views.pending_applications_view, name='pending_applications'),
    path('messages/', views.messages_view, name='messages'),
    path('helpdesk/', views.helpdesk_view, name='main_helpdesk'),
]

