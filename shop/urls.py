from django.urls import path
from shop import views



urlpatterns = [
        path('<slug:slug>/', views.index, name='shop'),
        path('<slug:slug>/inventory/', views.products_view, name='products'),
        path('<slug:slug>/dash/', views.shop_dash_view, name='shop_dash'),
        path('<slug:slug>/details/<str:pk>/', views.product_details_view, name='product_details'),
        path('<slug:slug>/cart/', views.cart_view, name='cart'),
        path('<slug:slug>/checkout/', views.checkout_view, name='checkout'),
        path('<slug:slug>/history/', views.history_view, name='history'),
        path('<slug:slug>/orders/<str:order_id>/', views.order_details_view, name='order_details'),
        path('<slug:slug>/categories/', views.categories_view, name='categories'),
        path('<slug:slug>/add_to_cart/<str:product_id>/', views.add_to_cart_view, name='add_to_cart_view'),
        path('<slug:slug>/clear_cart/', views.clear_cart_view, name='clear_cart'),
        path('<slug:slug>/wishlist/', views.wishlist_view, name='wishlist'),
        path('<slug:slug>/add_to_wishlist/<str:product_id>/', views.add_to_wishlist_view, name='add_to_wishlist_view'),
        path('<slug:slug>/contact_us/', views.helpdesk_view, name='shop_helpdesk'),
        path('<slug:slug>/about_us/', views.about_view, name='shop_about'),
        path('<slug:slug>/<str:model_name>/<int:object_id>/delete/', views.delete_view, name='shop_delete'),
        path('<slug:slug>/blog/', views.shop_blog_view, name='shop_blog'),
        path('<slug:slug>/blog/<str:postID>/', views.blog_details_view, name='blog_details'),
        path('<slug:slug>/addresses/', views.my_addresses_view, name='shop_addresses'),
        path('<slug:slug>/coupons/', views.coupons_view, name='coupons'),
        path('<slug:slug>/faqs/', views.faqs_view, name='shop_faqs'),
        path('<slug:slug>/return_items/<str:order_id>', views.returns_view, name='returns_page'),
        path('<slug:slug>/returns and cancellations', views.returns_and_cancellations_view, name='returns_and_cancellations'),
]




