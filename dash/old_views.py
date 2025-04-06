::from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from shop.models import Shop, ShopHelpDesk
from main.models import MainHelpDesk
from datetime import datetime
from datetime import timedelta
import logging
from dash.models import (
    Category,
    Inventory,
    Supplier,
    Delivery,
    PaymentMethod,
    Coupon,
    TodaysDeal,
    Profile,
    Role,
)


# Get logger
logger = logging.getLogger(__name__)


def my_shop(request):
    my_profile = Profile.objects.get(user=request.user)
    logger.debug(f'my shop: {my_profile.shop}')
    shop = Shop.objects.get(name=my_profile.shop.name)
    return shop

# Get % off
def percent_off(price, sale):
    return (float(sale) / 100) * float(price)


def index(request):
    context = {}
    return render(request, 'dash/index.html', context)


def categories(request):
    if request.method == 'POST':
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        avatar = request.FILES.get('avatar')
        source = request.POST.get('source')
        category_id = request.POST.get('category_id')
        is_featured = request.POST.get('is_featured')

        if source == 'new_category':
            Category.objects.create(shop=my_shop(request), category=category_name, description=description)
            messages.success(request, 'Category added')
            return redirect('categories')

        elif source == 'edit_category':
            category = get_object_or_404(Category, id=category_id)
            category.category = category_name
            category.description = description

            if is_featured:
                category.is_featured = is_featured

            if avatar:
                category.avatar = avatar

            category.save()
            messages.success(request, f'{category.category} Category edited')
            return redirect('categories')

    my_categories = Category.objects.filter(shop=my_shop(request))
    context = {'categories': my_categories}
    return render(request, 'dash/categories.html', context)


def inventory_view(request):
    if request.method == 'POST':
        product_name = request.POST.get('product')
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        units = request.POST.get('units')
        price = request.POST.get('price')
        is_featured = request.POST.get('is_featured')
        source = request.POST.get('source')
        product_id = request.POST.get('id')
        avatar = request.FILES.get('avatar')

        if category_name:
            category, created = Category.objects.get_or_create(category=category_name, shop=my_shop(request))

        if source == 'edit_product':
            product_obj = get_object_or_404(Inventory, id=product_id)
            product_obj.product = product_name
            product_obj.description = description
            product_obj.quantity = quantity
            product_obj.price = price
            product_obj.category = category
            
            if is_featured:
                product_obj.is_featured = is_featured

            if avatar:
                product_obj.avatar = avatar

            if units:
                product_obj.units = units

            product_obj.save()
            messages.success(request, f'{product_obj} edited')
            return redirect('inventory')

        elif source == 'new_product':
            Inventory.objects.create(
                shop = my_shop(request),
                product = product_name,
                category = category,
                description = description,
                quantity = quantity,
                units = units,
                price = price,
                is_featured = is_featured if is_featured else False,
                **({"avatar": avatar} if avatar else {}),
            )
            messages.success(request, f'{product_name} added to inventory')
            return redirect('inventory')

    products = Inventory.objects.filter(shop=my_shop(request), status='available')
    categories = Category.objects.filter(shop=my_shop(request))
    context = {'products': products, 'categories': categories}
    return render(request, 'dash/inventory.html', context)


def orders_view(request):
    if request.method == 'POST':
        product = request.POST.get('product')
        product_id = request.POST.get('product_id')
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        units = request.POST.get('units')
        source = request.POST.get('source')
        supplier_name = request.POST.get('supplier')
        order_id = request.POST.get('id')

        if supplier_name:
            supplier, sup_created = Supplier.objects.get_or_create(name=supplier_name, shop=my_shop(request))

        if category_name:
            category, created = Category.objects.get_or_create(category=category_name, shop=my_shop(request))

        if source == 'new_order':
            Inventory.objects.create(
                shop = my_shop(request),
                supplier = supplier,
                product = product,
                category = category,
                description = description,
                order_amount = quantity,
                units = units,
                status = 'ordered',
                available = False,
            )
            messages.success(request, f'Order for {quantity} {units} of {product} prepared.')
            return redirect('orders')

        elif source == 'new_order2':
            prod_instance = get_object_or_404(Inventory, product_id=product_id)
            prod_instance.order_amount = quantity
            prod_instance.status = 'ordered'
            prod_instance.supplier = supplier
            prod_instance.save()
            messages.success(request, f'Order for {quantity} {prod_instance} prepared.')
            return redirect('orders')

        elif source == 'edit_order':
            order = get_object_or_404(Inventory, id=order_id)
            order.supplier = supplier
            order.product = product
            order.category = category
            order.description = description
            order.quantity = quantity

            if units:
                order.units = units

            order.save()
            messages.success(request, f'Order for {quantity} {units} of {product} edited')
            return redirect('orders')

        elif source == 'receive':
            order = get_object_or_404(Inventory, id=order_id)
            order.description = 'None'
            order.status = 'available'
            order.quantity += order.order_amount
            order.order_amount = 0
            order.save()
            messages.success(request, f'{order.quantity} {order.units} of {order.product} added to inventory')
            return redirect('orders')
    
    all_products = Inventory.objects.filter(shop=my_shop(request))
    low_stocks = []

    for p in all_products:
        if p.quantity < 20:
            low_stocks.append(p)

    categories = Category.objects.filter(shop=my_shop(request))
    orders = all_products.filter(status='ordered')
    suppliers = Supplier.objects.filter(shop=my_shop(request))
    context = {
        'products': orders,
        'categories': categories,
        'suppliers': suppliers,
        'low_stock_products': low_stocks,
    }
    return render(request, 'dash/orders.html', context)


def deliveries_view(request):
    if request.method == 'POST':
        customer = request.POST.get('username')
        quantity = request.POST.get('quantity')
        source = request.POST.get('source')
        order_id = request.POST.get('id')
        phone = request.POST.get('phone')
        order_no = request.POST.get('order_number')
        product_id = request.POST.get('product_id')

        try:
            username = User.objects.get(username=customer)

        except User.DoesNotExist:
            username = None

        if source == 'new_delivery':
            selected_product = get_object_or_404(Inventory, product_id=product_id)
            category_instance = get_object_or_404(Category, category=selected_product.category.category)

            if int(quantity) < selected_product.quantity:
                Delivery.objects.create(
                    shop = my_shop(request),
                    username = username,
                    unregistered_user = customer,
                    order_number = order_no,
                    prod_id = selected_product.product_id,
                    category = category_instance,
                    product = selected_product,
                    quantity = quantity,
                    price = float(selected_product.price) - float(selected_product.discount),
                    units = selected_product.units,
                    total = (float(selected_product.price) - float(selected_product.discount)) * float(quantity),
                    phone = phone,
                )
                selected_product.quantity -= int(quantity)
                selected_product.save()
                messages.success(request, f'Delivery request for {quantity} {selected_product.units} of {selected_product.product} created.')

            else:
                messages.error(request, f'Only {selected_product.quantity} {selected_product.units} are available.')

            return redirect('deliveries')

        elif source == 'confirm_delivery':
            delivery = get_object_or_404(Delivery, id=order_id)
            delivery.status = 'confirmed'
            delivery.time_confirmed = datetime.now()
            delivery.admin = request.user
            delivery.save()
            messages.success(request, f'Delivery request for {delivery.quantity} {delivery.units} of {delivery.product.product} confirmed')
            return redirect('deliveries')

        elif source == 'confirm_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)
            
            for o in mult_orders:
                o.status = 'confirmed'
                o.time_confirmed = datetime.now()
                o.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_confirmed', 'admin'])
            messages.success(request, f'Order /#{order_no} confirmed')
            return redirect('deliveries')
    
    requests = Delivery.objects.filter(shop=my_shop(request), status='processing') 
    dash_requests = requests.filter(source='dash')
    cart_requests = requests.filter(source='cart')
    cart_requests = cart_requests.values('order_number', 'status').annotate(
        total_quantity=models.Sum('quantity'),
        total_price=models.Sum('price'),
        item_count=models.Count('id')
    )
    available_products = Inventory.objects.filter(shop=my_shop(request), status='available')
    context = {
        'available_products': available_products,
        'dash_requests': dash_requests,
        'cart_requests': cart_requests,
    }
    return render(request, 'dash/deliveries.html', context)


def confirmed_deliveries_view(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        source = request.POST.get('source')
        order_id = request.POST.get('id')
        driver_name = request.POST.get('driver')
        order_no = request.POST.get('order_number')

        if driver_name:
            driver, created = User.objects.get_or_create(shop=my_shop(request), username=driver_name)

            if created:
                logger.debug(driver)

        if source == 'assign_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)

            if address:
                order.address = address
            
            for order in mult_orders:
                order.status = 'in_transit'
                order.time_in_transit = datetime.now()
                order.driver = driver
                order.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_in_transit','driver', 'admin'])
            messages.success(request, f'Delivery #{order_no} assigned to {driver}')
            return redirect('confirmed_deliveries')
 
        elif source == 'complete_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)

            for order in mult_orders:
                order.status = 'completed'
                order.time_completed = datetime.now()
                order.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_completed', 'admin'])
            messages.success(request, f'Order #{order.order_number} completed')
            return redirect('confirmed_deliveries')

    # my_drivers = Profile.objects.filter(shop=my_shop(request), role='driver')
    my_drivers = []
    all_deliveries = Delivery.objects.filter(shop=my_shop(request))
    confirmed_deliveries = all_deliveries.filter(status='confirmed').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    deliveries_in_transit = all_deliveries.filter(status='in_transit').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    completed_deliveries = all_deliveries.filter(status='completed').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    context = {
        'confirmed_deliveries': confirmed_deliveries,
        'deliveries_in_transit': deliveries_in_transit,
        'completed_deliveries': completed_deliveries,
        'my_drivers': my_drivers,
    }
    return render(request, 'dash/confirmed_deliveries.html', context)


def track_order_view(request):
    context = {}
    return render(request, 'dash/track_order.html', context)


def order_details_view(request, order_id):
    orders = Delivery.objects.filter(order_number=order_id)
    context = {'orders': orders}
    return render(request, 'dash/order_details.html', context)


def online_sales_view(request):
    sales = Delivery.objects.filter(shop=my_shop(request), source='cart', status='completed')  
    online_sales = sales.values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    context = {'sales': online_sales}
    return render(request, 'dash/online_sales.html', context)


def physical_sales_view(request):
    if request.method == 'POST':
        customer = request.POST.get('username')
        phone = request.POST.get('phone')
        product_no = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        order_no = request.POST.get('order_number')
        payment_method = request.POST.get('payment_method')
        source = request.POST.get('source')

        if source == 'new_sale':
            sel_product = get_object_or_404(Inventory, product_id=product_no)
            payments = get_object_or_404(PaymentMethod, shop=my_shop(request), payment_method=payment_method)
            category = get_object_or_404(Category, shop=my_shop(request), category=sel_product.category.category)

            if int(quantity) < sel_product.quantity:
                Delivery.objects.create(
                    shop = my_shop(request),
                    unregistered_user = customer,
                    order_number = order_no,
                    product = sel_product,
                    prod_id = sel_product.product_id,
                    category = category,
                    quantity = quantity,
                    price = sel_product.price,
                    units = sel_product.units,
                    total = float(quantity) * float(sel_product.price),
                    phone = phone,
                    payment_method = payments,
                    source = 'in_shop',
                )
                sel_product.quantity -= int(quantity)
                sel_product.save()
                messages.success(request, f'Order {order_no} processing. Please confirm payment.')

            else:
                messages.error(request, f'Only {sel_product.quantity} {sel_product.units} are currently available.')

            return redirect('physical_sales')

        elif source == 'confirm_payment':
            mult_orders = Delivery.objects.filter(shop=my_shop(request), order_number=order_no)

            for order in mult_orders:
                order.status = 'completed'
                order.admin = request.user
                order.time_completed = datetime.now()

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_completed', 'admin',])
            messages.success(request, f'Order #{order_no} completed')
            return redirect('physical_sales')

    available_products = Inventory.objects.filter(shop=my_shop(request), status='available')
    pay_method = PaymentMethod.objects.filter(shop=my_shop(request))
    pending_sales = Delivery.objects.filter(
        shop = my_shop(request),
        source = 'in_shop',
        status = 'processing',
    ).values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id'),
    )
    completed_sales = Delivery.objects.filter(
        shop = my_shop(request),
        source = 'in_shop',
        status = 'completed',
    ).values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id'),
    )
    context = {
        'available_products': available_products,
        'pay_method': pay_method,
        'pending_sales': pending_sales,
        'completed_sales': completed_sales,
    }
    return render(request, 'dash/physical_sales.html', context)


def delete_view(request, pk):
    obj = get_object_or_404(Inventory, shop=my_shop(request), id=pk)

    if request.method == 'POST':
        # Delete product
        obj.delete()
        messages.success(request, f'{obj} deleted')
        return redirect('inventory')

    context = {'obj': obj}
    return render(request, 'dash/delete.html', context)


def main_helpdesk_view(request):
    shop = my_shop(request)
    tickets = MainHelpDesk.objects.filter(username=request.user)

    if request.method == 'POST':
        issue = request.POST.get('issue')
        description = request.POST.get('description')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        source = request.POST.get('source')

        if source == 'new_ticket':
            MainHelpDesk.objects.create(
                shop = shop,
                username = request.user,
                issue = issue,
                description = description,
                phone = phone,
                email = email,
            )
            messages.success(request, f'Ticket generated.')
            return redirect('main_helpdesk_user')
        
    context = {'tickets': tickets}
    return render(request, 'dash/main_helpdesk.html', context)


def shop_helpdesk_view(request):
    shop = my_shop(request)
    issues = ShopHelpDesk.objects.filter(shop=shop)
    pending_issues = issues.filter(is_sorted=False)
    sorted_issues = issues.filter(is_sorted=True)

    if request.method == 'POST':
        status = request.POST.get('status')
        is_sorted = request.POST.get('is_sorted')
        source = request.POST.get('source')
        tkt_id = request.POST.get('id')

        if source == 'change_status':
            ticket = get_object_or_404(ShopHelpDesk, id=tkt_id)
            ticket.status = status

            if is_sorted:
                ticket.is_sorted = is_sorted
                ticket.status = 'sorted'
            
            ticket.admin = request.user
            ticket.save()
            messages.success(request, f'Ticket {ticket.help_id}: {status}')
            return redirect('shop_helpdesk')

    context = {
        'issues': pending_issues,
        'sorted_issues': sorted_issues,
    }
    return render(request, 'dash/shop_helpdesk.html', context)


def shop_profile_view(request):
    shop = my_shop(request)
    staff_roles = Role.objects.filter(shop=shop)

    if request.method == 'POST':
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        avatar = request.FILES.get('avatar')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        location = request.POST.get('location')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        insta = request.POST.get('instagram')
        twitter = request.POST.get('twitter')
        role = request.POST.get('role_name')
        title1 = request.POST.get('title1')
        title2 = request.POST.get('title2')
        source = request.POST.get('source')

        if source == 'update_profile':
            shop.name = name
            shop.bio = bio
            shop.location = location
            shop.address = address
            shop.email = email
            shop.phone = phone
            shop.instagram = insta
            shop.twitter = twitter

            if avatar:
                shop.avatar = avatar

            if image1:
                shop.image1 = image1

            if image2:
                shop.image2 = image2

            shop.save()
            messages.success(request, 'Shop profile updated.')
            return redirect('shop_profile')

        elif source == 'settings_form':
            shop.title1 = title1
            shop.title2 = title2
            shop.save()

            if role:
                Role.objects.create(shop=shop, role_name=role)

            messages.success(request, 'Settings updated.')
            return redirect('shop_profile')

    context = {
        'my_shop': shop,
        'staff_roles': staff_roles,
    }
    return render(request, 'dash/shop_profile.html', context)


def deals_and_promos_view(request):
    shop = my_shop(request)
    all_products = Inventory.objects.filter(shop=shop)
    coupons = Coupon.objects.filter(shop=shop)
    all_categories = Category.objects.filter(shop=shop)

    if request.method == 'POST':
        product = request.POST.get('product')
        amount = request.POST.get('amount')
        source = request.POST.get('source')
        category_name = request.POST.get('category')
        coupon_id = request.POST.get('coupon_id')
        duration = request.POST.get('duration')
        deal_no = request.POST.get('deal_id')

        if product:
            product_instance = get_object_or_404(Inventory, product_id=product)

        if category_name:
            category_instance = get_object_or_404(Category, shop=shop, category=category_name)

        if source == 'new_discount':
            product_instance.discount = amount
            product_instance.in_deals = True
            product_instance.in_discount = True
            product_instance.price = float(product_instance.price) - float(amount)
            product_instance.save()
            messages.success(request, f'KSH. {amount} discount set for {product_instance.product}. Please confirm price.')
            return redirect('deals_and_promos')

        elif source == 'new_percent_off':
            product_instance.discount = percent_off(product_instance.price, amount)
            product_instance.in_deals = True
            product_instance.in_sale = True
            product_instance.percent_off = amount
            product_instance.price = float(product_instance.price) - float(product_instance.discount)
            product_instance.save()
            messages.success(request, f'{amount}% discount set for {product_instance.product}. Please confirm current price.')
            return redirect('deals_and_promos')

        elif source == 'new_category_sale':
            category_products = all_products.filter(category=category_instance)

            for product in category_products:
                product.discount = percent_off(product.price, int(amount))
                product.in_deals = True
                product.percent_off = amount
                product.price = float(product.price) - float(product.discount)

            Inventory.objects.bulk_update(category_products, ['discount', 'in_deals', 'percent_off', 'price'])
            category_instance.in_sale = True
            category_instance.percent_off = amount
            category_instance.save()
            messages.success(request, f'{amount}% discount set for all products in {category_name}. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'new_coupon':
            Coupon.objects.create(
                shop = shop,
                percent_off = amount,
            )
            messages.success(request, f'Coupon for {amount}% off on all shopping generated.')
            return redirect('deals_and_promos')

        elif source == 'new_todays_deal':
            product_instance.price = float(product_instance.price) - float(amount)
            product_instance.in_deals = True
            product_instance.discount = amount
            product_instance.save()

            TodaysDeal.objects.create(
                shop = shop,
                product_id = product_instance.product_id,
                product = product_instance.product,
                avatar = product_instance.avatar,
                discount = amount,
                time = timezone.now() + timedelta(hours=int(duration))
            )
            logger.debug(TimedDeal.objects.all())
            
            messages.success(request, f'{product_instance.product} saved as deal of the day')
            return redirect('deals_and_promos')

        elif source == 'cancel_discount':
            product_instance.in_deals = False
            product_instance.in_sale = False
            product_instance.in_discount = False
            product_instance.price += product_instance.discount
            product_instance.percent_off = 0
            product_instance.discount = 0
            product_instance.save()
            messages.success(request, f'Discount for {product_instance.product} cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_discounts':
            products = all_products.filter(in_discount=True)

            for p in products:
                p.in_deals = False
                p.in_discount = False
                p.price += p.discount
                p.discount = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_discount', 'discount', 'price'])
            messages.success(request, 'All discounts cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_sales':
            products = all_products.filter(in_sale=True)

            for p in products:
                p.in_deals = False
                p.in_sale = False
                p.price += p.discount
                p.discount = 0
                p.percent_off = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
            messages.success(request, 'All discounts cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_category_sale':
            products = all_products.filter(category=category_instance)

            for p in products:
                p.in_deals = False
                p.in_sale = False
                p.price += p.discount
                p.discount = 0
                p.percent_off = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
            category_instance.in_sale = False
            category_instance.percent_off = 0
            category_instance.save()
            messages.success(request, f'Sale for {category_instance.category} cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_category_sales':
            categories = all_categories.filter(in_sale=True)

            for c in categories:
                products = all_products.filter(category=c)

                for p in products:
                    p.in_deals = False
                    p.in_sale = False
                    p.price += p.discount
                    p.discount = 0
                    p.percent_off = 0

                Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
                c.in_sale = False
                c.percent_off = 0
                c.save()

            messages.success(request, 'All category sales cancelled. Please confirm prices.')
            return redirect('deals_and_promos')


        elif source == 'cancel_coupon':
            coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
            coupon.status = 'inactive'
            coupon.save()
            messages.success(request, f'Coupon #{coupon_id} deactivated.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_coupons':
            for coupon in coupons:
                coupon.status = 'inactive'

            Coupon.objects.bulk_update(coupons, ['status'])
            messages.success(request, 'All coupons deactivated.')
            return redirect('deals_and_promos')

        elif source == 'deactivate_todays_deal':
            deal = get_object_or_404(TimedDeal, id=deal_no)
            deal.status = 'inactive'
            deal.save()

            product = get_object_or_404(Inventory, product_id=deal.product_id)
            product.price += deal.discount
            product.discount = 0
            product.in_deals = False
            product.save()

            messages.success(request, f'Deal for {product.product} deactivated. Please confirm current price.')
            return redirect('deals_and_promos')

    todays_deals = TimedDeal.objects.filter(shop=shop)
    categories_no_sale = all_categories.filter(in_sale=False)
    available_products = all_products.filter(in_deals=False)
    in_discounts = all_products.filter(in_discount=True)
    in_sales = all_products.filter(in_sale=True)
    category_sales = all_categories.filter(in_sale=True)
    context = {
        'all_products': all_products,
        'products': available_products,
        'categories': categories_no_sale,
        'in_discounts': in_discounts,
        'in_sales': in_sales,
        'category_sales': category_sales,
        'coupons': coupons,
        'todays_deals':todays_deals,
    }
    return render(request, 'dash/deals_and_promos.html', context)


def staff_view(request):
    shop = my_shop(request)
    staff = Profile.objects.filter(shop=shop, in_staff=True)
    roles = Role.objects.filter(shop=shop)

    if request.method == 'POST':
        staff_username = request.POST.get('username')
        staff_email = request.POST.get('email')
        staff_password1 = request.POST.get('password1')
        staff_password2 = request.POST.get('password2')
        staff_role = request.POST.get('role')
        source = request.POST.get('source')

        if source == 'new_staff':
            if staff_password1 == staff_password2:
                User.objects.create(
                    username = staff_username,
                    email = staff_email,
                    password = staff_password1,
                )
                the_profile = get_object_or_404(User, username=staff_username)
                the_profile.set_password(staff_password1)
                the_profile.save()
                role = get_object_or_404(Role, shop=shop, role_name=staff_role)
                Profile.objects.create(
                    shop = shop,
                    in_staff = True,
                    user = the_profile,
                    role = role,
                )
                messages.success(request, 'New staff member registered')
                return redirect('dash_staff')

    context = {
        'staff': staff,
        'roles': roles,
    }
    return render(request, 'dash/staff.html', context)
