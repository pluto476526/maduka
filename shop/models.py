from django.utils.text import slugify
from django.db import models
import secrets
import string


# Create your models here.

class ShopCategory(models.Model):
    category = models.CharField(max_length=30)
    categoryID = models.CharField(max_length=10, null=True, blank=True, unique=True)
    
    def __str__(self):
        return self.category

    def save(self, *args, **kwargs):
        if not self.categoryID:
            self.categoryID = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(8))
        super().save(*args, **kwargs)


class Shop(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(blank=True, null=True)
    shopID = models.CharField(max_length=10, unique=True, null=True)
    bio = models.TextField(blank=True, null=True)
    logo = models.ImageField(default='logo.jpg')
    avatar1 = models.ImageField(default='shop1.jpg')
    avatar2 = models.ImageField(default='shop2.jpg')
    avatar3 = models.ImageField(default='shop3.jpg')
    title1 = models.CharField(max_length=50, default='Find Top Brands.')
    title2 = models.CharField(max_length=50, default='Exceptional Quality.')
    title3 = models.CharField(max_length=50, default='Shop With Ease')
    shop_category = models.ForeignKey('shop.ShopCategory', on_delete=models.SET_NULL, null=True, related_name='shop_category')
    location = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    instagram = models.CharField(max_length=50, blank=True, null=True)
    twitter = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
    total_sales = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if not self.shopID:
            self.shopID = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Cart(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    customer = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='processing') # processing, checkout, checked_out, in_wishes
    county = models.ForeignKey('shop.CountyShipped', on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    checked_out = models.DateTimeField(blank=True, null=True)
    coupon = models.ForeignKey('dash.Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer.username}'s cart"
    
    @property
    def original_price(self):
        """Calculate total price of all items in the cart without applying discounts or coupons"""
        return sum(item.total for item in self.items.all()) # related_name='items'

    @property
    def total_price(self):
        """Calculate the total price of all items in the cart after applying everything."""
        total = self.original_price
        if self.county:
            total = float(total) + self.county.price
        if self.coupon:
            total = float(total) * (1 - self.coupon.percent_off / 100)
        return max(total, 0)

 
class CartItem(models.Model):
    cart = models.ForeignKey('shop.Cart', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE, related_name='products')
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_deleted = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        """Automatically calculate the total price for the item."""
        self.total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.product} in {self.cart.id}"


class Ticket(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='shop')
    username = models.ForeignKey('auth.User', on_delete=models.CASCADE,  related_name='shopper')
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    issue = models.CharField(max_length=100)
    description = models.TextField()
    help_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    status = models.CharField(max_length=10, default='pending')
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='cc')
    is_sorted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.issue}'

    def save(self, *args, **kwargs):
        if not self.help_id:
            self.help_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class CountyShipped(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    county = models.CharField(max_length=50)
    price = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.county}'


class Address(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='addresses')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='user_addr')
    county = models.ForeignKey('shop.CountyShipped', on_delete=models.CASCADE, related_name='counties')
    town = models.CharField(max_length=20)
    street = models.CharField(max_length=20)
    house = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
       return f'{self.user}: {self.id}'


class BlogPost(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='author')
    blogID = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100)
    category = models.ForeignKey('shop.BlogCategory', on_delete=models.SET_NULL, null=True)
    # tags = models.ForeignKey()
    avatar = models.ImageField(default='blog.jpg')
    summary = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='blg_admin')
    comments = models.ForeignKey('shop.BlogComment', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending') # pending, confirmed, deleted
    is_featured = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.blogID}'

    def save(self, *args, **kwargs):
        if not self.blogID:
            self.blogID = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class BlogCategory(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    category = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.category}'


class BlogComment(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='commenter')
    post = models.ForeignKey('shop.BlogPost', on_delete=models.CASCADE, null=True, related_name='blog')
    comment = models.TextField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)



