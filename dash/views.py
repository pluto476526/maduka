from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.timezone import now as n
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from shop.models import Shop, Ticket, CountyShipped, BlogPost, BlogCategory, BlogComment
from main.models import MainHelpDesk, Notification
from datetime import datetime, timedelta, timezone
import logging
from dash.models import (
    Category,
    Inventory,
    Supplier,
    Delivery,
    DeliveryItem,
    PaymentMethod,
    Coupon,
    Profile,
    Role,
    Unit,
    LowStockThreshold,
    TodaysDeal,
    Transaction,
    HomePageSession,
)

# Logger setup
logger = logging.getLogger(__name__)

def get_user_shop(request):
    """Retrieve the shop associated with the current user's profile."""
    try:
        profile = Profile.objects.get(user=request.user)
        shop = Shop.objects.get(name=profile.shop.name)
        return shop
    except (Profile.DoesNotExist, Shop.DoesNotExist) as e:
        logger.error(f"Error retrieving shop: {e}")
        messages.error(request, "Shop not found.")
        return None


def percent_off(price, sale):
    """Calculate percentage off for a price."""
    try:
        return (float(sale) / 100) * float(price)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid input for percent_off: {e}")
        return 0


@login_required
def index(request):
    shop = get_user_shop(request)
    my_inventory = Inventory.objects.filter(shop=shop, status='available', is_deleted=False)
    my_deliveries = Delivery.objects.filter(shop=shop, status='completed', is_deleted=False)
    inventory_value = my_inventory.aggregate(total=models.Sum(models.F('price') * models.F('quantity')))['total']
    inventory_count = my_inventory.aggregate(total=models.Sum('quantity'))['total']

    popular_products = Inventory.objects.filter(
        del_product__delivery__shop=shop,
        del_product__delivery__status='completed'
    ).annotate(
        total_quantity=models.Sum('del_product__quantity'),
        sales=models.Sum(models.F('del_product__quantity') * models.F('price'))
    ).order_by('-sales')[:3]
    
    categories = Category.objects.filter(shop=shop, is_deleted=False).count()
    completed_sales = my_deliveries.aggregate(total=models.Sum('total'))['total']
    physical_sales = my_deliveries.filter(source='dash').aggregate(total=models.Sum('total'))['total']
    ecomm_sales = my_deliveries.filter(source='cart').aggregate(total=models.Sum('total'))['total']
    pending_tickets = Ticket.objects.filter(shop=shop, status='pending', is_deleted=False).count()
    team_members = Profile.objects.filter(shop=shop, in_staff=True, is_deleted=False).count()
    recent_transactions = Transaction.objects.filter(shop=shop, is_deleted=False)[:10]
    counties_shipped = CountyShipped.objects.filter(shop=shop, is_deleted=False).count()
    current_month = n().month
    current_year = n().year
    monthly_sales = my_deliveries.filter(time_completed__year=current_year, time_completed__month=current_month).aggregate(models.Sum('total')).get('total', 0)
    top_customers = Profile.objects.filter(shop=shop, is_deleted=False).order_by('-total_spent')[:5]
    my_profile = get_object_or_404(Profile, user=request.user)
    my_notifications = Notification.objects.filter(shop=shop, is_deleted=False)
    notifications = []
    if my_profile.is_admin == 'True':
        admin_notifications = my_notifications.filter(target='admin')
        other_notifications = my_notifications.filter(target='everyone')
        notitications.append(admin_notifications)
        notifications.append(other_notifications)
    elif my_profile.is_admin == 'False':
       notifications = my_notifications.filter(target='admin')
    
    sessions = HomePageSession.objects.filter(shop=shop)
    num_sessions = sessions.count()
    duration = sessions.filter(exit_time__isnull=False)
    average_duration = duration.aggregate(
        avg_duration = models.Avg(
            models.ExpressionWrapper(
                models.F('exit_time') - models.F('entry_time'),
                output_field = models.DurationField()
            )
        )
    )
    avg_duration_secs = average_duration['avg_duration'].total_seconds() if average_duration['avg_duration'] else 0


    # Get today's date (start of the day)
    today = n().date()

    # Filter transactions for today and sum the amounts
    total_sales_today = Transaction.objects.filter(
        timestamp__date = today, 
        is_deleted = False
    ).aggregate(total_sales = models.Sum('amount'))['total_sales'] or 0


    context = {
        'inventory_value': inventory_value,
        'inventory_count': inventory_count,
        'categories': categories,
        'completed_sales': completed_sales,
        'pending_tickets': pending_tickets,
        'team_members': team_members,
        'physical_sales': physical_sales,
        'ecomm_sales': ecomm_sales,
        'monthly_sales': monthly_sales,
        'counties_shipped': counties_shipped,
        'recent_transactions': recent_transactions,
        'popular_products': popular_products,
        'notifications': notifications,
        'num_sessions': num_sessions,
        'avg_duration': avg_duration_secs,
        'total_sales_today': total_sales_today,
        'top_customers': top_customers,
    }
    return render(request, 'dash/index.html', context)



@login_required
def categories(request):
    shop = get_user_shop(request) 
    my_categories = Category.objects.filter(shop=shop, is_deleted=False)

    if request.method == 'POST':
        category_name = request.POST.get('category', '').strip().lower()
        description = request.POST.get('description')
        avatar = request.FILES.get('avatar')
        source = request.POST.get('source')
        category_id = request.POST.get('category_id')
        is_featured = request.POST.get('is_featured')
        confirm_delete = request.POST.get('delete_cat')

        if category_id:
            category = get_object_or_404(Category, id=category_id)

        try:
            with transaction.atomic():
                if source == 'new_category':
                    Category.objects.create(
                        shop=shop,
                        category=category_name,
                        description=description,
                    )
                    messages.success(request, f"New Category '{category_name}' added.")

                elif source == 'edit_category':
                    category.category = category_name
                    category.description = description
                    if is_featured:
                        category.is_featured = True
                    if avatar:
                        category.avatar = avatar
                    category.save()
                    messages.success(request, f"{category.category} updated.")

                elif source == 'delete_category':
                    if confirm_delete:
                        category.is_deleted = True
                        category.save()
                        messages.success(request, f'{category.category} deleted.')
        
        except Exception as e:
            logger.error(f"Error in category operation: {e}")
            messages.error(request, "Failed to process the category.")
        return redirect('categories')

    return render(request, 'dash/categories.html', {'categories': my_categories})


@login_required
def inventory_view(request):
    shop = get_user_shop(request)
    products = Inventory.objects.filter(shop=shop, status='available', is_deleted=False)
    categories = Category.objects.filter(shop=shop, is_deleted=False)
    units = Unit.objects.filter(shop=shop, is_deleted=False)

            
    if request.method == 'POST':
        product_name = request.POST.get('product')
        category_name = request.POST.get('category', '').strip().lower()
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        units = request.POST.get('units', '').strip().lower()
        price = request.POST.get('price')
        is_featured = request.POST.get('is_featured')
        source = request.POST.get('source')
        product_id = request.POST.get('id')
        avatar = request.FILES.get('avatar')
        confirm_delete = request.POST.get('delete_item')

        if product_id:
            product = get_object_or_404(Inventory, id=product_id)
        
        with transaction.atomic():

            if category_name:
                category, _ = Category.objects.get_or_create(category=category_name, shop=shop)
            
            if product_id:
                product = get_object_or_404(Inventory, id=product_id)
            
            if units:
                unit, _ = Unit.objects.get_or_create(shop=shop, units=units)
            
            if source == 'edit_product':
                product.product = product_name
                product.category = category
                product.description = description
                product.quantity = quantity
                product.units = unit
                product.price = price
                if is_featured:
                    product.is_featured = True 
                if avatar:
                    product.avatar = avatar
                product.save()
                messages.success(request, f"Item '{product_name}' updated.")

            elif source == 'new_product':
                if not is_featured:
                    is_featured = False
                Inventory.objects.create(
                    shop = shop,
                    product = product_name,
                    category = category,
                    description = description,
                    quantity = quantity,
                    units = unit,
                    price = price,
                    is_featured = is_featured,
                    **({"avatar": avatar} if avatar else {}),
                )
                messages.success(request, f"Item '{product_name}' added to your inventory.")
            
            elif source == 'delete_item':
                if confirm_delete:
                    product.is_deleted = True
                    product.save()
                    messages.success(request, f'Item "{product.product}" deleted.')
        return redirect('inventory')

    context = {
        'products': products,
        'categories': categories,
        'units': units,
    }
    return render(request, 'dash/inventory.html', context)


@login_required
def orders_view(request):
    shop = get_user_shop(request)
    try:
        th = LowStockThreshold.objects.get(shop=shop)
        threshold = th.threshold
    except Exception:
        threshold = 0
    my_inventory = Inventory.objects.filter(shop=shop, is_deleted=False)
    low_stocks = my_inventory.filter(quantity__lt=threshold)
    orders = my_inventory.filter(in_orders=True)
    categories = Category.objects.filter(shop=shop, is_deleted=False)
    suppliers = Supplier.objects.filter(shop=shop, is_deleted=False)
    units = Unit.objects.filter(shop=shop, is_deleted=False)


    if request.method == 'POST':
        product = request.POST.get('product', '').strip().lower()
        product_id = request.POST.get('product_id')
        category_name = request.POST.get('category', '').strip().lower()
        instr = request.POST.get('instructions')
        quantity = request.POST.get('quantity')
        p_units = request.POST.get('units', '').strip().lower()
        source = request.POST.get('source')
        supplier_name = request.POST.get('supplier', '').strip().lower()
        order_id = request.POST.get('id')
        confirm_delete = request.POST.get('delete_item')
        
        try:
            if supplier_name:
                supplier, _ = Supplier.objects.get_or_create(shop=shop, name=supplier_name)

            if category_name:
                category, _ = Category.objects.get_or_create(shop=shop, category=category_name)

            if p_units:
                p_unit, _ = Unit.objects.get_or_create(shop=shop, units=p_units)
            
            if order_id:
                order = get_object_or_404(Inventory, id=order_id)

            if source == 'new_order':
                Inventory.objects.create(
                    shop = shop,
                    supplier = supplier,
                    product = product,
                    category = category,
                    order_instructions = instr,
                    order_amount = quantity,
                    units = p_unit,
                    status = 'ordered',
                    available = False,
                    in_orders = True,
                )
                messages.success(request, f"Order for {quantity} {p_units} of {product} prepared.")

            elif source == 'new_order2':
                prod_instance = get_object_or_404(Inventory, product_id=product_id)
                prod_instance.order_amount = quantity
                prod_instance.in_orders = True
                prod_instance.supplier = supplier
                prod_instance.order_instructions = instr
                prod_instance.save()
                messages.success(request, f"Order for {prod_instance.quantity} {prod_instance.product} prepared.")

            elif source == 'edit_order':
                order.supplier = supplier or order.supplier
                order.product = product
                order.category = category or order.category
                order.order_instructions = instr
                order.order_amount = quantity
                order.units = p_unit or order.units
                order.save()
                messages.success(request, f"Order for {order.quantity} {order.units.units} of {order.product} edited.")

            elif source == 'receive':
                order.status = 'available'
                order.quantity += order.order_amount
                order.order_amount = 0
                order.in_orders = False
                order.save()
                messages.success(request, f"{order.quantity} {order.units.units} of {order.product} added to inventory.")
            
            elif source == 'delete_order':
                if confirm_delete:
                    order.is_deleted = True
                    order.save()
                    messages.success(request, f"Order for {order.order_amount} {order.units.units} of {order.product} deleted.")

        except Exception as e:
            logger.error(f"Error processing order: {e}")
            messages.error(request, "Failed to process the order.")

        return redirect('orders')

    context = {
        'products': orders,
        'categories': categories,
        'suppliers': suppliers,
        'low_stock_products': low_stocks,
        'units': units,
    }
    return render(request, 'dash/orders.html', context)


@login_required
def deliveries_view(request):
    shop = get_user_shop(request)
    requests = Delivery.objects.filter(shop=shop, status='processing', is_deleted=False, is_delivery=True)
    dash_requests = requests.filter(source='dash')
    cart_requests = requests.filter(source='cart')
    available_products = Inventory.objects.filter(shop=shop, status='available', is_deleted=False)
    
    if request.method == 'POST':
        customer = request.POST.get('username')
        quantity = request.POST.get('quantity')
        source = request.POST.get('source')
        order_id = request.POST.get('o_id')
        phone = request.POST.get('phone')
        product_id = request.POST.get('product_id')
        confirm_delete = request.POST.get('delete_item')
        
        with transaction.atomic():
            if order_id:
                delivery = get_object_or_404(Delivery, id=order_id)
 
            if source == 'confirm_delivery':
                delivery.status = 'confirmed'
                delivery.time_confirmed = datetime.now()
                delivery.admin = request.user
                delivery.save()
                shop.total_sales += delivery.total
                shop.save()
                
                del_items = DeliveryItem.objects.filter(delivery=delivery)
                for d in del_items:
                    product = get_object_or_404(Inventory, id=d.product.id)
                    product.quantity -= d.quantity
                    product.total_sales += d.product.price
                    product.save()
                    
                    sale_category = Category.objects.filter(id=d.product.category.id)
                    for c in sale_category:
                        c.total_sales += delivery.total
                        c.save()

                messages.success(request, f'Delivery {delivery.order_number} confirmed.')
        
            elif source == 'delete_item':
                if confirm_delete:
                    delivery.is_deleted = True
                    delivery.save()
                    messages.success(request, f'Order "{delivery.order_number}" deleted.')

        return redirect('deliveries')
    
    context = {
        'available_products': available_products,
        'dash_requests': dash_requests,
        'cart_requests': cart_requests,
    }
    return render(request, 'dash/deliveries.html', context)


@login_required
@transaction.atomic
def confirmed_deliveries_view(request):
    shop = get_user_shop(request)
    all_deliveries = Delivery.objects.filter(shop=shop, is_deleted=False, is_delivery=True)
    confirmed_deliveries = all_deliveries.filter(status='confirmed')
    shipped_deliveries = all_deliveries.filter(status='shipped')
    completed_deliveries = all_deliveries.filter(status='completed')
    role = get_object_or_404(Role, shop=shop, role_name='driver')
    my_drivers = Profile.objects.filter(role=role)

    if request.method == 'POST':
        address = request.POST.get('address')
        source = request.POST.get('source')
        order_id = request.POST.get('id')
        driver_id = request.POST.get('driver')
        order_no = request.POST.get('order_number')
        confirm_delete = request.POST.get('delete_item')

        try:
            with transaction.atomic():

                if order_no:
                    order = get_object_or_404(Delivery, order_number=order_no)
                
                if source == 'assign_driver':
                    driver = get_object_or_404(Profile, id=driver_id)
                    order.status = 'shipped'
                    order.time_shipped = datetime.now()
                    order.driver = driver
                    order.admin = request.user
                    order.save()
                    messages.success(request, f"Delivery #{order_no} assigned to {driver.user.username}.")
                
                elif source == 'complete_order':
                    order.status = 'completed'
                    order.time_completed = datetime.now()
                    order.admin = request.user
                    order.save()
                    messages.success(request, f"Delivery #{order_no} marked as completed.")
                
                elif source == 'delete_item':
                    order.is_deleted = True
                    order.save()
                    messages.success(request, f'Delivery #{order.order_number} deleted.')

        except Exception as e:
            logger.error(f"Error processing delivery: {e}")
            messages.error(request, 'Error processing delivery.')
        return redirect('confirmed_deliveries')

    context = {
        'confirmed_deliveries': confirmed_deliveries,
        'shipped_deliveries': shipped_deliveries,
        'completed_deliveries': completed_deliveries,
        'my_drivers': my_drivers,
    }
    return render(request, 'dash/confirmed_deliveries.html', context)


@login_required
def track_order_view(request):
    return render(request, 'dash/track_order.html', {})


@login_required
def order_details_view(request, order_id):
    order = get_object_or_404(Delivery, order_number=order_id)
    orders = DeliveryItem.objects.filter(delivery=order)
    if not orders.exists():
        messages.error(request, f"No orders found for Order ID {order_id}.")
        return redirect('orders')
    context = {
        'order': order,
        'orders': orders,
    }
    return render(request, 'dash/order_details.html', context)


@login_required
def online_sales_view(request):
    shop = get_user_shop(request)
    online_sales = Delivery.objects.filter(shop=shop, source='cart', status='completed', is_deleted=False, is_delivery=True)
    context = {
        'online_sales': online_sales,
    }
    return render(request, 'dash/online_sales.html', context)


@login_required
@transaction.atomic
def physical_sales_view(request):
    shop = get_user_shop(request)
    available_products = Inventory.objects.filter(shop=shop, status='available', is_deleted=False)
    sales = Delivery.objects.filter(shop=shop, source='dash', is_deleted=False, is_delivery=False)
    pending_sales = sales.filter(status='processing')
    completed_sales = sales.filter(status='completed')
    p_method = PaymentMethod.objects.filter(shop=shop)
    
    if request.method == 'POST':
        customer = request.POST.get('username')
        phone = request.POST.get('phone')
        product_no = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 0)
        order_no = request.POST.get('order_number')
        payment_method = request.POST.get('payment_method')
        source = request.POST.get('source')
        confirm_delete = request.POST.get('delete_item')

        if product_no:
            sel_product = get_object_or_404(Inventory, product_id=product_no)
       
        if order_no:
            delivery = get_object_or_404(Delivery, order_number=order_no)
        
        with transaction.atomic():
            if source == 'new_sale':
                if int(quantity) > sel_product.quantity:
                    messages.error(request, f"Insufficient stock for item '{sel_product.product}'. Only {sel_product.quantity} {sel_product.units.units} are available.")
                    return redirect('physical_sales')

                payments = get_object_or_404(PaymentMethod, shop=shop, method=payment_method)
                totals = float(quantity) * float(sel_product.price)
                delivery = Delivery.objects.create(
                    shop=shop,
                    unregistered_user=customer,
                    total=totals,
                    phone=phone,
                    payment_method=payments,
                    source='dash',
                    is_delivery=False,
                )
                DeliveryItem.objects.create(delivery=delivery, product=sel_product, quantity=float(quantity))
                Transaction.objects.create(shop=shop, user=customer, amount=delivery.total, order=delivery)
                messages.success(request, f"Order {order_no} created. Please confirm payment.")
            
            elif source == 'add_product':
                if int(quantity) > sel_product.quantity:
                    messages.error(request, f'Insufficient stock for {sel_product}.')
                    return redirect('physical_sales')
                
                DeliveryItem.objects.create(delivery=delivery, product=sel_product, quantity=float(quantity))
                messages.success(request, f'Item "{sel_product.product}" added to order number {order_no}')
                
            elif source == 'confirm_payment':
                delivery.status = 'completed'
                delivery.time_completed = datetime.now()
                delivery.admin = request.user
                delivery.save()
                trans = get_object_or_404(Transaction, order=delivery)
                trans.status = 'completed'
                trans.admin = request.user
                trans.save()
                shop.total_sales += float(delivery.total) 
                shop.save()

                d_items = DeliveryItem.objects.filter(delivery=delivery)
                for d in d_items:
                    product = get_object_or_404(Inventory, id=d.product.id)
                    product.quantity -= d.quantity
                    product.total_sales += d.product.price
                    product.save()
                    
                    category = get_object_or_404(Category, id=d.product.category.id)
                    category.total_sales += float(d.total)
                    category.save()
                
                messages.success(request, f"Order '{order_no}' payment confirmed.")
            
            elif source == 'delete_item':
                if confirm_delete:
                    delivery.is_deleted = True
                    delivery.save()
                    messages.success(request, f'Order "{delivery.order_number}" deleted.')
        
        return redirect('physical_sales')

    context = {
        'available_products': available_products,
        'p_method': p_method,
        'pending_sales': pending_sales,
        'completed_sales': completed_sales,
    }
    return render(request, 'dash/physical_sales.html', context)


@login_required
def main_helpdesk_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    tickets = MainHelpDesk.objects.filter(username=request.user)

    if request.method == 'POST':
        issue = request.POST.get('issue', '').strip()
        description = request.POST.get('description', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        source = request.POST.get('source', '').strip()

        if source == 'new_ticket':
            MainHelpDesk.objects.create(
                shop=shop,
                username=request.user,
                issue=issue,
                description=description,
                phone=phone,
                email=email,
            )
            messages.success(request, "Ticket generated.")
            return redirect('main_helpdesk_user')

    return render(request, 'dash/main_helpdesk.html', {'tickets': tickets})


@login_required
def shop_helpdesk_view(request):
    shop = get_user_shop(request)
    issues = Ticket.objects.filter(shop=shop, is_deleted=False)
    pending_issues = issues.filter(is_sorted=False)
    sorted_issues = issues.filter(is_sorted=True)

    if request.method == 'POST':
        status = request.POST.get('status', '').strip().lower()
        is_sorted = request.POST.get('is_sorted')
        source = request.POST.get('source')
        tkt_id = request.POST.get('id')
        confirm_delete = request.POST.get('delete_item')

        if tkt_id:
            ticket = get_object_or_404(Ticket, id=tkt_id)
        
        with transaction.atomic():
            if source == 'change_status':
                if is_sorted:
                    ticket.is_sorted = True
                ticket.status = status
                ticket.admin = request.user
                ticket.save()
                messages.success(request, f'Ticket "{ticket.help_id}": {ticket.status}')
            
            if source == 'delete_item':
                if confirm_delete:
                    ticket.is_deleted = True
                    ticket.save()
                    messages.success(request, f'Ticket "{ticket.help_id} deleted."')

        return redirect('shop_helpdesk')

    context = {'issues': pending_issues, 'sorted_issues': sorted_issues}
    return render(request, 'dash/shop_helpdesk.html', context)


@login_required
@transaction.atomic
def shop_profile_view(request):
    shop = get_user_shop(request)
    staff_roles = Role.objects.filter(is_deleted=False, shop=shop)
    units = Unit.objects.filter(is_deleted=False, shop=shop)
    pm_methods = PaymentMethod.objects.filter(is_deleted=False, shop=shop)
    counties = CountyShipped.objects.filter(is_deleted=False, shop=shop)
    
    try:
        threshold = get_object_or_404(LowStockThreshold, shop=shop)
    except Exception:
        threshold = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        bio = request.POST.get('bio', '').strip()
        location = request.POST.get('location', '').strip()
        address = request.POST.get('address', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        insta = request.POST.get('instagram', '').strip()
        twitter = request.POST.get('twitter', '').strip()
        avatar1 = request.FILES.get('avatar1')
        avatar2 = request.FILES.get('avatar2')
        avatar3 = request.FILES.get('avatar3')
        title1 = request.POST.get('title1', '').strip()
        title2 = request.POST.get('title2', '').strip()
        title3 = request.POST.get('title3', '').strip()
        role = request.POST.get('role_name', '').strip()
        new_units = request.POST.get('units', '').strip()
        ls_threshold = request.POST.get('ls_threshold', '').strip()
        new_pm_method = request.POST.get('p_mthd')
        county = request.POST.get('county', '').strip()
        shipping_cost = request.POST.get('shipping_cost', '').strip()
        source = request.POST.get('source', '').strip()

        with transaction.atomic():
            if source == 'update_profile':
                shop.name = name
                shop.bio = bio
                shop.location = location
                shop.address = address
                shop.email = email
                shop.phone = phone
                shop.instagram = insta
                shop.twitter = twitter

                if avatar1:
                    shop.avatar1 = avatar1
                if avatar2:
                    shop.avatar2 = avatar2
                if avatar3:
                    shop.avatar3 = avatar3

                shop.save()
                messages.success(request, 'Shop profile updated.')

            elif source == 'settings_form':
                shop.title1 = title1
                shop.title2 = title2
                shop.title3 = title3
                shop.save()

                if role:
                    Role.objects.create(shop=shop, role_name=role)
                    messages.success(request, f'Staff role "{role}" added.')

                if new_units:
                    Unit.objects.create(shop=shop, units=new_units)
                    messages.success(request, f'Product units "{new_units}" added.')

                if new_pm_method:
                    PaymentMethod.objects.create(shop=shop, method=new_pm_method)
                    messages.success(request, f'Payment method "{new_pm_method}" added.')

                if ls_threshold:
                    if threshold:
                        threshold.threshold = ls_threshold
                        threshold.save()
                    else:
                        LowStockThreshold.objects.create(shop=shop, threshold=ls_threshold)
                        messages.success(request, f'Low stock threshold set at "{ls_threshold}".')

                if county:
                    CountyShipped.objects.create(shop=shop, county=county, price=shipping_cost)
                    messages.success(request, f'{county} registered.')

                messages.success(request, "Settings updated.")

        return redirect('shop_profile')

    context = {
        'my_shop': shop,
        'staff_roles': staff_roles,
        'units': units,
        'threshold': threshold,
        'p_methods': pm_methods or [],
        'counties': counties,
    }
    return render(request, 'dash/shop_profile.html', context)


@login_required
def deals_and_promos_view(request):
    shop = get_user_shop(request)
    all_products = Inventory.objects.filter(shop=shop, status='available', is_deleted=False)
    coupons = Coupon.objects.filter(shop=shop, is_deleted=False)
    all_categories = Category.objects.filter(shop=shop, is_deleted=False)
    todays_deals = TodaysDeal.objects.filter(shop=shop, is_deleted=False)
    categories_no_sale = all_categories.filter(in_sale=False)
    available_products = all_products.filter(in_deals=False)
    in_discounts = all_products.filter(in_discount=True)
    in_sales = all_products.filter(in_sale=True)
    category_sales = all_categories.filter(in_sale=True)
    
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
            product_instance.price -= int(amount)
            product_instance.in_deals = True
            product_instance.discount = amount
            product_instance.save()

            new = TodaysDeal.objects.create(
                shop = shop,
                product = product_instance,
                avatar = product_instance.avatar1,
                discount = amount,
                time = datetime.now(timezone(timedelta(hours=3))) + timedelta(hours=int(duration)+3)
            )
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
            deal = get_object_or_404(TodaysDeal, id=deal_no)
            deal.is_active = False
            deal.save()

            product = get_object_or_404(Inventory, product_id=deal.product_id)
            product.price += deal.discount
            product.discount = 0
            product.in_deals = False
            product.save()

            messages.success(request, f'Deal for {product.product} deactivated. Please confirm current price.')
            return redirect('deals_and_promos')

    
    context = {
        'all_products': all_products,
        'products': available_products,
        'categories': categories_no_sale,
        'in_discounts': in_discounts,
        'in_sales': in_sales,
        'category_sales': category_sales,
        'coupons': coupons,
        'todays_deals': [{'object': d,'app_label': d._meta.app_label, 'model_name': d._meta.model_name} for d in todays_deals],
    }
    return render(request, 'dash/deals_and_promos.html', context)


@login_required
@transaction.atomic
def staff_view(request):
    shop = get_user_shop(request)
    staff = Profile.objects.filter(shop=shop, in_staff=True, is_deleted=False)
    roles = Role.objects.filter(shop=shop, is_deleted=False)
    
    if request.method == 'POST':
        username = request.POST.get('name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role_name = request.POST.get('role', '').strip().lower()
        source = request.POST.get('source')
        staffID = request.POST.get('staffID')
        avatar = request.FILES.get('avatar')
        confirm_delete = request.POST.get('delete_item')

        if staffID:
            profile = get_object_or_404(Profile, id=staffID)
            user = get_object_or_404(User, profile=profile)
        
        if role_name:
            role, _ = Role.objects.get_or_create(shop=shop, role_name=role_name)

        with transaction.atomic():
            match source:
                case 'new_staff':
                    if password1 == password2:
                        user = User.objects.create_user(username=username, email=email, password=password1)
                        Profile.objects.create(shop=shop, user=user, in_staff=True, role=role)
                        messages.success(request, "New staff member created.")
                    
                    else:
                        messages.error(request, "Password mismatch or invalid input.")
                
                case 'edit_staff':
                    if avatar:
                        profile.avatar = avatar
                    profile.role = role
                    profile.save()
                    user.username = username
                    user.save()
                    messages.success(request, f'{profile.user.username}`s profile updated.')

                case 'delete_item':
                    if confirm_delete:
                        profile.is_deleted = True
                        profile.save()
                        messages.success(request, f'"{profile.user.username}" deleted.')
        
        return redirect('dash_staff')
    
    context = {
        'staff': staff,
        'roles': roles,
    }
    return render(request, 'dash/staff.html', context)



# @method_decorator(login_required, name='dispatch')
def delete_view(request, app_label, model_name, object_id):
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
        content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
        model = content_type.model_class()

        # Get the object instance
        obj = get_object_or_404(model, id=object_id)

        # Check user permissions (Optional: Customize this logic)
        if not request.user.is_superuser and hasattr(obj, 'shop'):
            if obj.shop != request.user.profile.shop:
                return HttpResponseForbidden("You do not have permission to delete this item.")

        if request.method == 'POST':
            # obj.delete()
            obj.is_deleted = True
            obj.save()
            messages.success(request, f"{model_name} with ID {object_id} has been deleted.")
            return redirect(request.POST.get('referer'))  # Adjust redirection as needed

        # Render a confirmation page
        context = {'object': obj, 'model_name': model_name, 'referer': referer}
        return render(request, 'dash/dash_delete.html', context)

    except ContentType.DoesNotExist:
        messages.error(request, "Invalid model type.")
        return redirect(referer) # Adjust redirection as needed


@login_required
def transactions_view(request):
    shop = get_user_shop(request)
    transactions = Transaction.objects.filter(shop=shop, is_deleted=False)
    context = {
        'transactions': transactions,
    }
    return render(request, 'dash/transactions.html', context)


@login_required
def blog_categories_view(request):
    shop = get_user_shop(request)
    categories = BlogCategory.objects.filter(shop=shop, is_deleted=False)

    if request.method == 'POST':
        category = request.POST.get('category','').strip().lower()
        source = request.POST.get('source')
        categoryID = request.POST.get('cat_id')
        confirm_delete = request.POST.get('delete_item')

        if categoryID:
            category = get_object_or_404(BlogCategory, id=categoryID)
        
        if source == 'new_category':
            BlogCategory.objects.create(shop=shop, category=category)
            messages.success(request, f'{category} category added.')
            return redirect('blog_categories')

        elif source == 'edit_category':
            cat.category = category
            cat.save()
            messages.success(request, f'Category updated.')
            return redirect('blog_categories')

        elif source == 'delete_item':
            if confirm_delete:
                category.is_deleted = True
                category.save()
                messages.success(request, f'Category "{category.category}" deleted.')
                return redirect('blog_categories')

    context = {
        'categories': categories,
    }
    return render(request, 'dash/blog_categories.html', context)


@login_required
def pending_posts_view(request):
    shop = get_user_shop(request)
    pending_posts = BlogPost.objects.filter(shop=shop, status='pending', is_deleted=False)
    categories = BlogCategory.objects.filter(shop=shop, is_deleted=False)

    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        is_featured = request.POST.get('is_featured')
        source = request.POST.get('source')
        avatar = request.FILES.get('avatar')
        post_id = request.POST.get('post_id')
        confirm_delete = request.POST.get('delete_item')
        
        if not is_featured:
                is_featured = False

        if category:
            category = get_object_or_404(BlogCategory, id=category)
        
        if post_id:
            post = get_object_or_404(BlogPost, id=post_id)

        if not avatar:
            avatar = 'blog.jpg'

        if source == 'new_post':
            BlogPost.objects.create(shop=shop, author=request.user, title=title, category=category, avatar=avatar, summary=summary, content=content, is_featured=is_featured)
            messages.success(request, 'Blogpost created.')
            return redirect('pending_posts')

        elif source == 'edit_post':
            post.title = title
            post.category = category
            post.summary = summary
            post.content = content
            if avatar:
                post.avatar = avatar
            if is_featured:
                post.is_featured = is_featured
            post.save()
            messages.success(request, 'BlogPost #{post.blogID} edited.')
            return redirect('pending_posts')

        elif source == 'confirm_post':
            post.status = 'confirmed'
            post.save()
            messages.success(request, 'BlogPost #{post.blogID} confirmed and posted.')
            return redirect('pending_posts')

        elif source == 'delete_item':
            if confirm_delete:
                post.is_deleted = True
                post.save()
                messages.success(request, f'BlogPost #{post.blogID} deleted')

    context = {
        'pending_posts': pending_posts,
        'categories': categories,
    }
    return render(request, 'dash/pending_posts.html', context)


@login_required
def confirmed_posts_view(request):
    shop = get_user_shop(request)
    confirmed_posts = BlogPost.objects.filter(shop=shop, status='confirmed', is_deleted=False)

    if request.method == 'POST':
        postID = request.POST.get('post_id')
        source = request.POST.get('source')
        confirm_delete = request.POST.get('delete_item')

        if postID:
            post = get_object_or_404(BlogPost, id=postID)

        with transaction.atomic():
            match source:
                case 'delete_item':
                    post.is_deleted = True
                    post.save()
                    messages.success(request, f'BlogPost #{post.blogID} deleted.')

        return redirect('confirmed_posts')
        
    context = {
        'confirmed_posts': confirmed_posts,
    }
    return render(request, 'dash/confirmed_posts.html', context)


@login_required
def removed_posts_view(request):
    shop = get_user_shop(request)
    deleted_posts = BlogPost.objects.filter(shop=shop, is_deleted=True)
    context = {
        'deleted_posts': deleted_posts,
    }
    return render(request, 'dash/removed_posts.html', context)

