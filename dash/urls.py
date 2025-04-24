from django.urls import path
from dash import views



urlpatterns = [
    path('', views.index, name='dash'),
    path('categories/', views.categories, name='categories'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('orders/', views.orders_view, name='orders'),
    path('deliveries/', views.deliveries_view, name='deliveries'),
    path('confirmed_deliveries/', views.confirmed_deliveries_view, name='confirmed_deliveries'),
    path('track_order/', views.track_order_view, name='track_order'),
    path('order/<str:order_id>/', views.order_details_view, name='order_details'),
    path('sales/online/', views.online_sales_view, name='online_sales'),
    path('sales/physical/', views.physical_sales_view, name='physical_sales'),
    path('helpdesk/shop/', views.main_helpdesk_view, name='main_helpdesk_user'),
    path('helpdesk/user/', views.shop_helpdesk_view, name='shop_helpdesk'),
    path('profile/', views.shop_profile_view, name='shop_profile'),
    path('promotional_sales/', views.deals_and_promos_view, name='deals_and_promos'),
    path('staff/', views.staff_view, name='dash_staff'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('pending_posts/', views.pending_posts_view, name='pending_posts'),
    path('confirmed_posts/', views.confirmed_posts_view, name='confirmed_posts'),
    path('removed_posts/', views.removed_posts_view, name='removed_posts'),
    path('blog_categories/', views.blog_categories_view, name='blog_categories'),
    path('delete/<str:app_label>/<str:model_name>/<int:object_id>/', views.delete_view, name='dash_delete'),
]



