# dash/context_processors.py

from django.contrib import messages
from django.db.models import Q
from dash.models import Delivery, Profile, Category
from shop.models import Shop, Cart, CartItem
import logging

logger = logging.getLogger(__name__)


def my_shop(request):
    """
    Retrieve the shop associated with the authenticated user's profile.
    Returns None if no shop is found.
    """
    # if not request.user.is_authenticated:
    #     return None

    try:
        profile = Profile.objects.get(user=request.user)
        if profile and profile.shop:
            return profile.shop
        return None

    except Exception as e:
        logger.error(f"Error retrieving shop for user {request.user}: {e}")
    return None


def the_shop(request):
    """
    Add the current user's shop to the context if authenticated.
    """
    try:
        shop = my_shop(request)
        if shop:
            return {'the_shop': shop}
    except Exception as e:
        logger.error(e)
    return {}


def get_categories(request):
    """
    This function helps display categories on the shop nav bar
    """
    try:
        shop = my_shop(request)
        sp_categories = Category.objects.filter(shop=shop, is_deleted=False)
        context = {'sp_categories': sp_categories}
        return context
    except Exception as e:
        logger.error(e)
    return {}


def cart_items_count(request):
    """
    This function gets the total number of cart items for the logged in user
    """
    try:
        shop = my_shop(request)
        my_cart = Cart.objects.filter(shop=shop, customer=request.user, status='processing', is_deleted=False).last()
        cart_items = CartItem.objects.filter(cart=my_cart).count() or 0
        context = {'cart_items_count': cart_items}
        return context
    except Exception as e:
        logger.debug(e)
        return {}


def shop_sidebar_stats(request):
    """
    This function provides context data for a shop sidebar(shop_dash)
    """
    try:
        shop = my_shop(request)
        orders = Delivery.objects.filter(shop=shop, username=request.user, is_deleted=False)
        completed_orders = orders.filter(status='completed').count() or 0
        wishlist = Cart.objects.filter(shop=shop, customer=request.user, status='in_wishes', is_deleted=False).count() or 0
        context = {
            'num_orders': orders.count() or 0,
            'completed_del': completed_orders,
            'wishlist': wishlist,
        }
        return context
    except Exception as e:
        logger.debug(e)
    return {}

def get_order(request):
    """
    Add tracked orders to the context based on a query parameter.
    """
    if not request.user.is_authenticated:
        return {}

    query = request.GET.get('q', '').strip()
    if not query:
        return {}

    try:
        shop = my_shop(request)
        if not shop:
            logger.warning("Shop is not available for the user.")
            return {}

        # Filter orders by shop and query
        orders = Delivery.objects.filter(shop=shop, order_number__icontains=query)
        if not orders.exists():
            messages.error(request, f'Order number "{query}" not found.')
            return {'tracked_order': []}

        return {'tracked_order': orders}
    except Exception as e:
        logger.error(f"Error retrieving orders for query '{query}': {e}")
    return {}

