# shop/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.db import transaction
from django.contrib.auth.decorators import login_required
from shop.models import Shop, Cart, CartItem, Ticket, CountyShipped, Address, BlogPost, BlogCategory, BlogComment
from dash.models import Inventory, Category, PaymentMethod, Delivery, DeliveryItem, TodaysDeal, Profile, Review, Coupon, Transaction
from main.models import Notification
from datetime import datetime, timedelta, timezone
import logging
import secrets
import string


# Logger setup
logger = logging.getLogger(__name__)

# Helper function: Retrieve a shop by name
def get_shop(slug):
    return get_object_or_404(Shop, slug=slug)


# Helper: Add product to cart
def add_to_cart(request, shopID, product_no, quantity=1):
    # Get the shop
    the_shop = get_object_or_404(Shop, id=shopID)
    
    # Get the product
    product = get_object_or_404(Inventory, product_id=product_no)
    
    # Ensure the user has an active cart
    cart, created = Cart.objects.get_or_create(
        shop = the_shop,
        customer = request.user,
        status = 'processing',
    )

    # Check if the product is already in the cart
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    
    if cart_item:
        messages.info(request, f'{product.product} is already in your cart.')
        return
    else:
        # Otherwise, add a new CartItem
        CartItem.objects.create(
            cart = cart,
            product = product,
            quantity = quantity,
        )
        messages.success(request, f"{product.product} added to your cart.")
        return

# View: Empty cart
def clear_cart_view(request, slug):
    the_shop = get_shop(slug)
    my_carts = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing', is_deleted=False)
    
    if request.method == 'POST':
        for c in my_carts:
            c.is_deleted = True
            c.status = 'deleted'
            c.save()
        messages.success(request, 'Cart cleared.')
        return redirect('cart', the_shop.slug)
    return render(request, 'shop/clear_cart.html', {})


# HELPER: Add product to wishlist
def add_to_wishlist(request, shopID, product_no):
    # Get the shop
    the_shop = get_object_or_404(Shop, id=shopID)
    
    # Get the product
    product = get_object_or_404(Inventory, product_id=product_no)
    
    # Ensure the user has an active cart
    cart, created = Cart.objects.get_or_create(
        shop = the_shop,
        customer = request.user,
        status = 'in_wishes',
    )

    # Check if the product is already in the wish list
    wish_item = CartItem.objects.filter(cart=cart, product=product, is_deleted=False).last()
    
    if wish_item:
        messages.info(request, f'{product.product} is already in your wish list.')
        return
    else:
        # Otherwise, add a new CartItem
        CartItem.objects.create(
            cart = cart,
            product = product,
            quantity = 1,
        )
        messages.success(request, f"{product.product} added to your wish list.")
        return


# View: Add to cart from the index page
def add_to_cart_view(request, slug, product_id):
    shop = get_shop(slug)
    add_to_cart(request, shop.id, product_id)
    return redirect(request.META.get('HTTP_REFERER'))
    context = {}
    return render(request, 'empty.html', context)


# View: Add to wishlist from the index page
def add_to_wishlist_view(request, slug, product_id):
    shop = get_shop(slug)
    add_to_wishlist(request, shop.id, product_id)
    return redirect(request.META.get('HTTP_REFERER'))
    context = {}
    return render(request, 'empty.html', context)


# View: Shop homepage
def index(request, slug):
    # Retrieve the shop and user profile
    shop = get_shop(slug)
    profile = get_object_or_404(Profile, user=request.user)

    # Fetch categories
    categories = Category.objects.filter(shop=shop, is_deleted=False)
    top_categories = categories.order_by('-total_sales')[:4]
    f_categories = categories.filter(is_featured=True).order_by('-timestamp')[:3]

    # Fetch products from top categories(tc) excluding those in the user's pending cart
    my_cart = Cart.objects.filter(shop=shop, customer=request.user, status='processing', is_deleted=False).last()
    cart_products = CartItem.objects.filter(cart=my_cart, is_deleted=False).values_list('product_id', flat=True)
    
    tc_products = []
    for t in top_categories:
        cat = get_object_or_404(Category, category=t.category)
        products = Inventory.objects.filter(shop=shop, category=cat, is_deleted=False).exclude(id__in=cart_products)[:3]
        for p in products:
            tc_products.append(p)

    # Fetch the 2 most recent deals of the day
    deals = TodaysDeal.objects.filter(shop=shop).order_by('-time')[:2]
    active_deals = []
    for d in deals:
        if d.time > datetime.now(timezone(timedelta(hours=3))):
            active_deals.append(d)

    # Fetch latest arrivals
    products = Inventory.objects.filter(shop=shop).exclude(id__in=cart_products)
    arrivals = products.order_by('-timestamp')[:4]

    # Fetch 4 featured products
    f_products = products.filter(is_featured=True).order_by('-timestamp')[:4]

    # Fetch 3 latest blogposts
    recent_posts = BlogPost.objects.filter(shop=shop, status='confirmed', is_deleted=False).order_by('-timestamp')[:3]
   
    # Prepare context for rendering
    context = {
        'profile': profile,
        'top_categories': top_categories,
        'f_categories': f_categories,
        'f_products': f_products,
        'tc_products': tc_products,
        'deals': active_deals,
        'new_arrivals': arrivals,
        'the_shop': shop,
        'recent_posts': recent_posts,
        # 'referer': request.META.get('HTTP_REFERER')
    }
    return render(request, 'shop/index.html', context)

    
# View: Products list
@login_required
def products_view(request, slug):
    sort_by = request.GET.get('sort_by', 'newest')
    show_count = int(request.GET.get('show', 12))
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Get shop object
    the_shop = get_shop(slug)

    # Current users cart for this shop
    my_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing').first()

    # Get all product IDs in the current user's cart for this shop
    cart_items = CartItem.objects.filter(cart=my_cart).values_list('product_id', flat=True)

    # Get all products excluding the ones already in the user's cart
    products = Inventory.objects.filter(
        is_deleted = False,
        status = 'available',
        shop = the_shop
    ).exclude(id__in=cart_items)


    categories = Category.objects.filter(is_deleted=False, shop=the_shop).annotate(
        product_count=Count('inventory')
    )
    grouped_products = [
        {
            'category': c,
            'c_products': products.filter(category=c),
            'count': c.product_count,
        }
        for c in categories
    ]
   
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    match sort_by:
        case 'newest':
            products = products.order_by('-timestamp')
        case 'best_sellers':
            products = products.order_by('-total_sales')
        case 'top_rated':
            products = products.order_by('-rating')
        case 'lowest_price':
            products = products.order_by('price')
        case 'highest_price':
            products = products.order_by('-price')
        case _:
            products = products.order_by('-timestamp')

    products = products[:show_count] # Limit no. of products to display

    if request.method == 'POST':
        prod_id = request.POST.get('id')
        source = request.POST.get('source')

        match source:
            case 'add_to_wishlist':
                add_to_wishlist(request, the_shop.id, prod_id)
                return redirect('products', the_shop.slug)
            case 'add_to_cart':
                add_to_cart(request, the_shop.id, prod_id, 1)
                return redirect('products', the_shop.slug)

    context = {
        'the_shop': the_shop,
        'products': products,
        'group': grouped_products,
        'sort_by': sort_by,
        'show_count': show_count,
    }
    return render(request, 'shop/products.html', context)

# View: Product details
@login_required
def product_details_view(request, slug, pk):
    sort_reviews = request.GET.get('sort_reviews', 'best_ratings')
    the_shop = get_shop(slug)
    product = get_object_or_404(Inventory, product_id=pk, shop=the_shop)
    rel_products = Inventory.objects.filter(is_deleted=False, shop=the_shop, category=product.category).exclude(product_id=product.product_id)[:4]
    reviews = Review.objects.filter(productID=product)

    match sort_reviews:
        case 'best_ratings':
            reviews = reviews.order_by('-rating')
        case 'worst_ratings':
            reviews = reviews.order_by('rating')
        case _:
            pass
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        email = request.POST.get('email')
        comment = request.POST.get('comment')
        body = request.POST.get('body')
        rating = request.POST.get('rating')
        source = request.POST.get('source')
        referer = request.META.get('HTTP_REFERER')
        logger.debug(rating)
        
        match source:
            case 'new_review':
                if not rating:
                    messages.error(request, 'Please rate the item.')
                    return redirect('product_details', the_shop.name, product.product_id)

                Review.objects.create(
                    user = request.user,
                    productID = product,
                    email = email or request.user.email,
                    comment = comment,
                    body = body,
                    rating = rating,
                )
                messages.success(request, 'New review added.')
                Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'New review from "{request.user.username}" on item: "{product.product}".', target='admin')

                return redirect('product_details', the_shop.name, product.product_id)
            case 'add_to_cart':
                add_to_cart(request, the_shop.name, product.product_id, quantity)
                return redirect(referer)
            case _:
                pass

    context = {
        'product': product,
        'the_shop': the_shop,
        'rel_products': rel_products,
        'reviews': reviews,
    }
    return render(request, 'shop/product_details.html', context)

# View: Cart
@login_required
def cart_view(request, slug):
    referer = request.META.get('HTTP_REFERER')
    the_shop = get_shop(slug)
    my_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing', is_deleted=False).first()
    cart_items = CartItem.objects.filter(cart=my_cart)
    counties = CountyShipped.objects.filter(is_deleted=False, shop=the_shop)

    if request.method == 'POST':
        cart_ids = request.POST.getlist('cart_pid[]')
        quantities = request.POST.getlist('quantity[]')
        note = request.POST.get('note')
        source = request.POST.get('source')
        cnty_id = request.POST.get('county')

        if source == 'add_county':
            county = get_object_or_404(CountyShipped, pk=cnty_id)
            my_cart.county = county
            my_cart.save()
            messages.success(request, 'Shipping costs calculated.')
            return redirect('cart', slug=the_shop.slug)

        elif source == 'add_note':
            my_cart.note = note
            my_cart.save()
            messages.success(request, 'Delivery note updated.')
            return redirect('cart', slug=the_shop.slug)

        elif source == 'edit_quantity':
            # Bulk update cart items
            for cart, quantity in zip(cart_ids, quantities):
                try:
                    quantity = max(1, min(int(quantity), 100))
                    product = get_object_or_404(Inventory, product_id=cart)
                    cart_item = cart_items.get(product=product)
                    cart_item.quantity = quantity
                    cart_item.save()
                except (Cart.DoesNotExist, ValueError):
                    messages.error(request, "Invalid cart update request.")

            messages.success(request, "Cart updated successfully.")
            return redirect('cart', slug=the_shop.slug)
       
        elif source == 'checkout_btn':
            if my_cart.county:
                my_cart.status = 'checkout'
                my_cart.save()
                messages.success(request, 'Please fill the details below to complete checkout.')
                Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'Cart checked out by "{request.user.username}".', target='admin')

                return redirect('checkout', slug=the_shop.slug)
            else:
                messages.error(request, 'Please select your county and calculate shipping costs.')
                return redirect('cart', slug=the_shop.slug)

    context = {
        'referer': referer,
        'counties': counties,
        'my_cart': my_cart,
        'the_shop': the_shop,
        'cart_items': [{'objects': cart, 'model_name': cart._meta.model_name} for cart in cart_items],
    }
    return render(request, 'shop/cart.html', context)

# View: Checkout
@login_required
def checkout_view(request, slug):
    the_shop = get_shop(slug)
    counties = CountyShipped.objects.filter(shop=the_shop, is_deleted=False)
    payment_methods = PaymentMethod.objects.filter(shop=the_shop)
    my_cart = Cart.objects.filter(is_deleted=False, shop=the_shop, customer=request.user, status='checkout').first()
    cart_items = CartItem.objects.filter(cart=my_cart, is_deleted=False)
    all_addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user)
    default_addr = all_addresses.filter(is_default=True).first()
    addresses = []
   
    if my_cart:
        addresses = all_addresses.filter(county=my_cart.county)
    
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")

    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        countyID = request.POST.get('countyID')
        town = request.POST.get('town')
        street = request.POST.get('street')
        house = request.POST.get('house')
        payment_method = request.POST.get('payment')
        source = request.POST.get('source')
        addr_id = request.POST.get('addr_id')
        cpn = request.POST.get('coupon')
           
        match source:
            case 'new_address':
                county = get_object_or_404(CountyShipped, id=countyID)
                Address.objects.create(shop=the_shop, user=request.user, county=county, town=town, street=street, house=house)
                messages.success(request, f'New address in {county.county} saved.')
                return redirect('checkout', the_shop.slug)
            case 'edit_default_addr':
                all_addresses.update(is_default=False)
                obj = get_object_or_404(Address, pk=addr_id)
                obj.is_default = True
                obj.save()
                messages.success(request, 'Default address updated.')
                return redirect('checkout', the_shop.slug)
            case 'coupon_form':
                if cpn:
                    coupon = get_object_or_404(Coupon, coupon_id=cpn)
                    if coupon and coupon.is_active:
                        my_cart.coupon = coupon
                        my_cart.save()
                        messages.success(request, f'{coupon.percent_off}% discount applied.')
                        return redirect('checkout', the_shop.slug)
                    elif not coupon.is_active:
                        messages.error(request, 'Coupon is not active.')
                        return redirect('checkout', the_shop.slug)
                    else:
                        messages.error(request, 'Please check coupon number.')
                        return redirect('checkout', the_shop.slug)
                else:
                    return redirect('checkout', the_shop.slug)
            case 'place_order':
                with transaction.atomic():
                    p_method = get_object_or_404(PaymentMethod, id=payment_method)
                    county = get_object_or_404(CountyShipped, id=my_cart.county.id)
                    logger.debug(f'cn: {county}, def_addr: {default_addr}')
                    if not default_addr:
                        messages.error(request, 'Please set shipping address.')
                        return redirect('checkout', the_shop.slug)
                    if default_addr.county.id != my_cart.county.id:
                        messages.error(request, f'Default shipping address must be located in {my_cart.county.county}.')
                        return redirect('checkout', the_shop.slug)
                    # Create or get the delivery
                    delivery = Delivery.objects.create(username=request.user, shop=the_shop)
                    delivery.note = my_cart.note
                    delivery.county = county
                    delivery.address = default_addr
                    delivery.payment_method = p_method
                    delivery.total = my_cart.total_price
                    delivery.source = 'cart'
                    delivery.save()
                    Transaction.objects.create(shop=the_shop, user=request.user, order=delivery, amount=delivery.total)

                    # Add items to the delivery
                    for i in cart_items:
                        product = get_object_or_404(Inventory, shop=the_shop, id=i.product.id)
                        DeliveryItem.objects.create(
                            delivery = delivery,
                            product = product,
                            quantity = i.quantity
                        )

                    # Update cart status
                    my_cart.status = 'checked_out'
                    my_cart.checked_out = datetime.now()
                    my_cart.save()

                messages.success(request, 'Check out completed.')
                Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'New order placed by "{request.user.username}".', target='admin')

                return redirect('checkout', the_shop.slug)
            case 'cancel_order':
                my_cart.is_deleted = True
                my_cart.save()
                messages.success(request, 'Order cancelled.')
                Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'"{request.user.username}" has cancelled his order.', target='admin')

                return redirect('shop', the_shop.slug)

    context = {
        'the_shop': the_shop,
        'counties': counties,
        'addresses': addresses,
        'default_addr': default_addr,
        'payment_methods': payment_methods,
        'my_cart': my_cart,
        'cart_items': [{'objects': cart, 'model_name': cart._meta.model_name} for cart in cart_items],
    }
    return render(request, 'shop/checkout.html', context)


# View: Order history
@login_required
def history_view(request, slug):
    the_shop = get_shop(slug)
    orders = Delivery.objects.filter(shop=the_shop, username=request.user, is_deleted=False)
    context = {
        'the_shop': the_shop,
        'orders': orders,
    }
    return render(request, 'shop/history.html', context)


# View: Order details
@login_required
def order_details_view(request, slug, order_id):
    the_shop = get_shop(slug)
    order = get_object_or_404(Delivery, order_number=order_id)
    orders = DeliveryItem.objects.filter(delivery=order, is_deleted=False)
    address = Address.objects.filter(shop=the_shop, user=request.user, is_default=True).first()
    shipping = get_object_or_404(CountyShipped, id=order.county.id)
    total_amnt = float(order.total) - float(shipping.price)
    context = {
        'the_shop': the_shop, 
        'order': order,
        'orders': orders,
        'address': address,
        'shipping': shipping,
        'total_amnt': total_amnt,
    }
    return render(request, 'shop/order_details.html', context)


# View: Wishlist
@login_required
def wishlist_view(request, slug):
    the_shop = get_shop(slug)
    my_carts = Cart.objects.filter(customer=request.user, shop=the_shop, is_deleted=False)
    active_cart = my_carts.filter(status='processing').last()
    cart_items = CartItem.objects.filter(cart=active_cart, is_deleted=False).values_list('id', flat=True)
    wish_cart = my_carts.filter(status='in_wishes').last()
    wishes = CartItem.objects.filter(cart=wish_cart, is_deleted=False).exclude(id__in=cart_items)
    
    if request.method == 'POST':
        wish_item = request.POST.get('id')
        itemID = request.POST.get('itemID')
        source = request.POST.get('source')

        if itemID:
            item = get_object_or_404(CartItem, id=itemID)

        if source == 'add_to_cart':
            add_to_cart(request, the_shop.id, wish_item)
            item.is_deleted = True
            item.save()
            return redirect('wishlist', the_shop.slug)
        
        if source == 'delete_item':
            item.is_deleted = True
            item.save()
            messages.success(request, f'Item "{item.product.product}" removed from wishlist.')
            return redirect('wishlist', the_shop.slug)

    context = {
        'the_shop': the_shop,
        'wishes': wishes,
    }
    return render(request, 'shop/wishlist.html', context)

# View: Categories
@login_required
def categories_view(request, slug):
    the_shop = get_shop(slug)
    categories = Category.objects.filter(shop=the_shop)
    context = {
        'the_shop': the_shop,
        'categories': categories,
    }
    return render(request, 'shop/categories.html', context)


@login_required
def helpdesk_view(request, slug):
    the_shop = get_shop(slug)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        issue = request.POST.get('issue')
        description = request.POST.get('description')
        source = request.POST.get('source')

        if source == 'send_issue':
            Ticket.objects.create(
                shop = the_shop,
                username = request.user,
                phone = phone,
                email = email,
                issue = issue,
                description = description,
            )
            messages.success(request, 'Message sent. A team member will reply as soon as possible.')
            Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'"{request.user.username}" has submitted a message.', target='admin')

            return redirect('shop_helpdesk', the_shop.slug)

    issues = Ticket.objects.filter(username=request.user)
    context = {
        'the_shop': the_shop,
        'issues': issues,
    }
    return render(request, 'shop/contact_us.html', context)


@login_required
def about_view(request, slug):
    the_shop = get_shop(slug)
    staff = Profile.objects.filter(shop=the_shop, in_staff=True, is_deleted=True)
    context = {
        'the_shop': the_shop,
        'staff': staff,
    }
    return render(request, 'shop/about.html', context)


@login_required
# @method_decorator(login_required, name='dispatch')
def delete_view(request, slug, model_name, object_id):
    """
    Universal delete view for any model.
    Parameters:
        app_label: The name of the app (e.g., 'shop').
        model_name: The name of the model (e.g., 'Product').
        object_id: The ID of the object to delete.
    """
    referer = request.META.get('HTTP_REFERER')

    try:
        # Get the model class
        content_type = ContentType.objects.get(model=model_name.lower())
        model = content_type.model_class()

        # Get the object instance
        obj = get_object_or_404(model, id=object_id)

        # Check user permissions
        if not request.user.is_superuser and hasattr(obj, 'shop'):
            if obj.shop != request.user.profile.shop:
                return HttpResponseForbidden("You do not have permission to delete this item.")

        if request.method == 'POST':
            # obj.delete()
            obj.is_deleted = True
            obj.save()
            messages.success(request, f"{obj} has been deleted.")
            return redirect(request.POST.get('referer_url'))

        # Render a confirmation page
        context = {
            'object': obj,
            'model_name': model_name,
            'referer': referer,
        }
        return render(request, 'shop/delete.html', context)

    except ContentType.DoesNotExist:
        messages.error(request, "Invalid model type.")
        return redirect(referer)


@login_required
def my_addresses_view(request, slug):
    the_shop = get_shop(slug)
    addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user)
    counties = CountyShipped.objects.filter(is_deleted=False, shop=the_shop)

    if request.method == 'POST':
        town = request.POST.get('town')
        street = request.POST.get('street')
        house = request.POST.get('house')
        source = request.POST.get('source')
        addressID = request.POST.get('addressID')
        set_default = request.POST.get('set_default')
        countyID = request.POST.get('countyID')
        
        if countyID:
            county = get_object_or_404(CountyShipped, id=countyID)
        
        if source == 'new_address':
            Address.objects.create(
                shop = the_shop,
                user = request.user,
                county = county,
                town = town,
                street = street,
                house = house,
            )
            messages.success(request, f'New address in {county.county}, {town} created.')
            return redirect('shop_addresses', the_shop.slug)

        elif source == 'edit_address':
            addr = get_object_or_404(Address, pk=addressID)
            addr.county = county
            addr.town = town
            addr.street = street
            addr.house = house
            if set_default:
                addresses.update(is_default=False)
                addr.is_default = True
            addr.save()
            messages.success(request, 'Address updated.')
            return redirect('shop_addresses', the_shop.slug)

    context = {
        'the_shop': the_shop,
        'addresses': addresses,
        'counties': counties,
    }
    return render(request, 'shop/my_addresses.html', context)


# View: return single items page
def returns_view(request, slug, order_id):
    shop = get_shop(slug)
    delivery = get_object_or_404(Delivery, order_number=order_id)
    delivery_items = DeliveryItem.objects.filter(delivery=delivery, status='none', is_deleted=False)

    if request.method == 'POST':
        item_ids = request.POST.getlist('item_id[]')
        return_note = request.POST.get('return_note')
        source = request.POST.get('source')
        
        match source:
            case 'return_items':
                with transaction.atomic():
                    if return_note:
                        delivery.return_note = return_note
                        delivery.save()

                    for i in item_ids:
                        item = delivery_items.filter(id=i).first()
                        item.status = 'returned'
                        item.save()
                        messages.success(request, f'{item.product.product} set for return.')
                    Notification.objects.create(shop=the_shop, origin=request.user, n_type='alert', message=f'"{request.user.username}" wants to return an item.', target='admin')

                    return redirect('returns_page', shop.slug, order_id)
    context = {
        'delivery_items': delivery_items,
        'the_shop': shop,
    }
    return render(request, 'shop/returns_page.html', context)


# View: Returns and cancellations
def returns_and_cancellations_view(request, slug):
    shop = get_shop(slug)
    my_deliveries = Delivery.objects.filter(shop=shop, username=request.user)
    returns = my_deliveries.filter(status='cancelled')
    returned_items = DeliveryItem.objects.filter(delivery__in=my_deliveries, status='returned')
    context = {
        'the_shop': shop,
        'returns': returns,
        'returned_items': returned_items,
    }
    return render(request, 'shop/returns_and_cancellations.html', context)


# View: Shop mini dashboard -> userstats
def shop_dash_view(request, slug):
    shop = get_shop(slug)
    default_addr = Address.objects.filter(shop=shop, user=request.user, is_default=True).first()
    orders = Delivery.objects.filter(shop=shop, username=request.user, is_deleted=False)
    completed_orders = orders.filter(status='completed').count() or 0
    cancelled_orders = orders.filter(status='cancelled').count() or 0
    context = {
        'address': default_addr,
        'recent_orders': orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'the_shop': shop,
    }
    return render(request, 'shop/shop_dash.html', context)


def shop_blog_view(request, slug):
    shop = get_shop(slug)
    posts = BlogPost.objects.filter(shop=shop, status='confirmed', is_deleted=False)
    recent_posts = posts.order_by('timestamp')[:3]
    categories = BlogCategory.objects.filter(shop=shop, is_deleted=False)
    context = {
        'the_shop': shop,
        'posts': posts,
        'recent_posts': recent_posts,
        'categories': categories,
    }
    return render(request, 'shop/blog.html', context)


def blog_details_view(request, slug, postID):
    shop = get_shop(slug)
    post = get_object_or_404(BlogPost, blogID=postID)
    comments = BlogComment.objects.filter(shop=shop, post=post, is_deleted=False)

    if request.method == 'POST':
        comment = request.POST.get('comment')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        source = request.POST.get('source')

        if source == 'new_comment':
            BlogComment.objects.create(shop=shop, author=request.user, post=post, comment=comment, phone=phone, email=email)
            Notification.objects.create(shop=shop, origin=request.user, n_type='alert', message=f'New comment from "{request.user.username}": "{comment}".', target='admin')
            messages.success(request, 'Comment posted.')
            return redirect('blog_details', shop.slug, postID)
    context = {
        'the_shop': shop,
        'post': post,
        'comments': comments,
    }
    return render(request, 'shop/blog_details.html', context)


def coupons_view(request, slug):
    shop = get_shop(slug)
    coupons = Coupon.objects.filter(shop=shop, is_active=True, is_deleted=False)
    context = {
        'the_shop': shop,
        'coupons': coupons,
    }
    return render(request, 'shop/coupons.html', context)


def faqs_view(request, slug):
    context = {}
    return render(request, 'shop/faqs.html', context)
