# Generated by Django 5.1.3 on 2025-03-21 21:38

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_shop_avatar3'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ShopHelpDesk',
            new_name='Ticket',
        ),
    ]
