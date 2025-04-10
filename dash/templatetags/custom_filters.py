# dash/templatetags.py

from django import template
from shop.models import Cart, CartItem, Shop


register = template.Library()


@register.filter
def format_time(value):
    if value is None or 0:
        return '0m: 0s'

    minutes = value // 60
    seconds = int(value % 60)

    if minutes == 0:
        return f'0m: {seconds}s'
    return f'{minutes}m: {seconds}s'


@register.simple_tag(takes_context=True)
def get_cart_items_count(context, slug):
    request = context['request']
    if not request.user.is_authenticated:
        return 0
    shop = Shop.objects.get(slug=slug)
    cart = Cart.objects.filter(shop=shop, customer=request.user, status='processing', is_deleted=False).last()
    return CartItem.objects.filter(cart=cart).count() if cart else 0

