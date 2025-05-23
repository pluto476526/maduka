# Generated by Django 5.1.3 on 2025-05-19 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('avatar', models.ImageField(default='category.jpg', upload_to='')),
                ('in_sale', models.BooleanField(default=False)),
                ('percent_off', models.PositiveIntegerField(default=0)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percent_off', models.PositiveIntegerField()),
                ('coupon_id', models.CharField(max_length=11, unique=True)),
                ('status', models.CharField(default='active', max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unregistered_user', models.CharField(blank=True, max_length=50, null=True)),
                ('order_number', models.CharField(blank=True, max_length=10, null=True)),
                ('avatar', models.ImageField(default='shop1.jpg', upload_to='')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('time_confirmed', models.DateTimeField(blank=True, null=True)),
                ('time_shipped', models.DateTimeField(blank=True, null=True)),
                ('time_completed', models.DateTimeField(blank=True, null=True)),
                ('time_cancelled', models.DateTimeField(blank=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('return_note', models.TextField(blank=True, null=True)),
                ('source', models.CharField(default='dash', max_length=10)),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_delivery', models.BooleanField(default=True)),
                ('status', models.CharField(default='processing', max_length=20)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_deleted', models.BooleanField(default=False)),
                ('status', models.CharField(default='none', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='HomePageSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessionID', models.CharField(max_length=40)),
                ('entry_time', models.DateTimeField(auto_now_add=True)),
                ('exit_time', models.DateTimeField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('ip_addr', models.GenericIPAddressField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar1', models.ImageField(default='pd1.jpg', upload_to='')),
                ('avatar2', models.ImageField(default='pd2.jpg', upload_to='')),
                ('avatar3', models.ImageField(default='pd3.jpg', upload_to='')),
                ('avatar4', models.ImageField(default='pd4.jpg', upload_to='')),
                ('avatar5', models.ImageField(default='pd5.jpg', upload_to='')),
                ('product', models.CharField(max_length=50)),
                ('product_id', models.CharField(max_length=10, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.PositiveIntegerField(default=0)),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(default='available', max_length=20)),
                ('is_featured', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('in_deals', models.BooleanField(default=False)),
                ('in_discount', models.BooleanField(default=False)),
                ('in_sale', models.BooleanField(default=False)),
                ('discount', models.PositiveIntegerField(default=0)),
                ('percent_off', models.PositiveIntegerField(default=0)),
                ('available', models.BooleanField(default=False)),
                ('order_amount', models.PositiveIntegerField(default=0)),
                ('order_instructions', models.TextField(blank=True, null=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
                ('in_orders', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LowStockThreshold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.PositiveIntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=10, null=True, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('access_level', models.PositiveIntegerField(default=3)),
                ('bio', models.TextField(blank=True, null=True)),
                ('avatar', models.ImageField(default='user.jpg', upload_to='')),
                ('in_staff', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('total_spent', models.PositiveIntegerField(default=0)),
                ('facebook', models.CharField(blank=True, max_length=255, null=True)),
                ('insta', models.CharField(blank=True, max_length=255, null=True)),
                ('twitter', models.CharField(blank=True, max_length=255, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('last_seen', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('comment', models.CharField(max_length=100)),
                ('body', models.TextField(blank=True, null=True)),
                ('rating', models.DecimalField(decimal_places=1, default=0, max_digits=3)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TodaysDeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('discount', models.PositiveIntegerField(default=0)),
                ('time', models.DateTimeField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transactionID', models.CharField(max_length=10, unique=True)),
                ('user', models.CharField(max_length=20)),
                ('amount', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(default='processing', max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('units', models.CharField(max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
    ]
