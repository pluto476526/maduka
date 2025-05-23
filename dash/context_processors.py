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
    if not request.user.is_authenticated:
        return {}


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
    if not request.user.is_authenticated:
        return {'the_shop': None}
    try:
        shop = my_shop(request)
        if shop:
            return {'the_shop': shop}
    except Exception as e:
        logger.error(e)
    return {}


def shop_sidebar_stats(request):
    """
    This function provides context data for a shop sidebar(shop_dash)
    """
    if not request.user.is_authenticated:
        return {}


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


