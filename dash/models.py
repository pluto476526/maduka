from django.db import models
from django.utils import timezone
import secrets, string


class Role(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    role_name = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.role_name}'


class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    identifier = models.CharField(max_length=10, unique=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    access_level = models.PositiveIntegerField(default=3) # 1-> basic access, 2-> key operations, 3-> full access
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(default='user.jpg')
    shop = models.ForeignKey('shop.Shop', on_delete=models.SET_NULL, blank=True, null=True)
    in_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    total_spent = models.PositiveIntegerField(default=0)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    insta = models.CharField(max_length=255, blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Supplier(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.name}'
    

class Category(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    avatar = models.ImageField(default='category.jpg')
    in_sale = models.BooleanField(default=False)
    percent_off = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.category}'


class Unit(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    units = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.units}'


class LowStockThreshold(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    threshold = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.threshold}'


class Inventory(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    avatar1 = models.ImageField(default='pd1.jpg')
    avatar2 = models.ImageField(default='pd2.jpg')
    avatar3 = models.ImageField(default='pd3.jpg')
    avatar4 = models.ImageField(default='pd4.jpg')
    avatar5 = models.ImageField(default='pd5.jpg')
    product = models.CharField(max_length=50)
    product_id = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey('dash.Category', on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    units = models.ForeignKey('dash.Unit', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='available') # available
    is_featured = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    in_deals = models.BooleanField(default=False)
    in_discount = models.BooleanField(default=False)
    in_sale = models.BooleanField(default=False)
    discount = models.PositiveIntegerField(default=0)
    percent_off = models.PositiveIntegerField(default=0)
    # options = 
    supplier = models.ForeignKey('dash.Supplier', on_delete=models.SET_NULL, blank=True, null=True)
    available = models.BooleanField(default=False)
    order_amount = models.PositiveIntegerField(default=0)
    order_instructions = models.TextField(blank=True, null=True)
    total_sales = models.PositiveIntegerField(default=0)
    in_orders = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.product}'

    def save(self, *args, **kwargs):
        if not self.product_id:
            self.product_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    productID = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE)
    comment = models.CharField(max_length=100)
    body = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.productID}: {self.comment}'


class PaymentMethod(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    method = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.shop}: {self.method}'



class Delivery(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    username = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='customer', null=True, blank=True)
    unregistered_user = models.CharField(max_length=50, blank=True, null=True)
    order_number = models.CharField(max_length=10, blank=True, null=True)
    avatar = models.ImageField(default='shop1.jpg')
    timestamp = models.DateTimeField(auto_now_add=True)
    time_confirmed = models.DateTimeField(blank=True, null=True)
    time_shipped = models.DateTimeField(blank=True, null=True)
    time_completed = models.DateTimeField(blank=True, null=True)
    time_cancelled = models.DateTimeField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=False, blank=True, null=True)
    county = models.ForeignKey('shop.CountyShipped', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.ForeignKey('shop.Address', on_delete=models.SET_NULL, blank=True, null=True)
    payment_method = models.ForeignKey('dash.PaymentMethod', on_delete=models.SET_NULL, blank=True, null=True)
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='admin')
    driver = models.ForeignKey('dash.Profile', on_delete=models.SET_NULL, blank=True, null=True, related_name='staff')
    note = models.TextField(blank=True, null=True)
    return_note = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=10, default='dash') # dash, cart
    is_deleted = models.BooleanField(default=False)
    is_delivery = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='processing') # processing, confirmed, shipped, accepted_by_driver, declined_by_driver, completed, cancelled
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.username}'s delivery"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        super().save(*args, **kwargs)

class DeliveryItem(models.Model):
    delivery = models.ForeignKey('dash.Delivery', on_delete=models.CASCADE, related_name='items', null=True)
    product = models.ForeignKey('dash.Inventory', on_delete=models.SET_NULL, related_name='del_product', null=True)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='none') # none, cancelled, returned

    def save(self, *args, **kwargs):
        """Automatically calculate the total price of the item"""
        if self.product:
            self.total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product} x {self.quantity} (Total: {self.total})'

class Coupon(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    percent_off = models.PositiveIntegerField()
    coupon_id = models.CharField(max_length=11, unique=True)
    status = models.CharField(max_length=10, default='active') # active, inactive
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.percent_off}'

    def save(self, *args, **kwargs):
        if not self.coupon_id:
            self.coupon_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        super().save(*args, **kwargs)


class TodaysDeal(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    product = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE, null=True, related_name='deal')
    avatar = models.ImageField(default='dp1.jpg')
    discount = models.PositiveIntegerField(default=0)
    time = models.DateTimeField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.product.product_id}'


class Transaction(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=10, unique=True)
    user = models.CharField(max_length=20)
    order = models.ForeignKey('dash.Delivery', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='processing') #processing, completed
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.transactionID}'

    def save(self, *args, **kwargs):
        if not self.transactionID:
            self.transactionID = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        super().save(*args, **kwargs)


class HomePageSession(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    sessionID = models.CharField(max_length=40)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_addr = models.GenericIPAddressField(blank=True, null=True)

    # class Meta:
    #     unique_together = ('shop', 'sessionID')

    @property
    def duration_seconds(self):
        if self.exit_time:
            return (self.exit_time - self.entry_time).total_seconds()
        return None

    def __str__(self):
        return f'{self.shop}: {self.sessionID}'


