# Generated by Django 5.1.3 on 2025-04-06 01:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_alter_shop_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='discount',
        ),
    ]
