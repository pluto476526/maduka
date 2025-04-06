from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from web import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('sign_in/', views.sign_in, name='sign_in'),
    path('sign_out/', views.sign_out, name='sign_out'),
    path('shops/', views.all_shops_view, name='all_shops'),
    path('shops/<slug:slug>/', views.shop_details_view, name='shop_details'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
