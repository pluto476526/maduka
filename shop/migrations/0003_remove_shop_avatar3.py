# Generated by Django 5.1.3 on 2025-03-08 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_alter_shop_avatar3'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='avatar3',
        ),
    ]
