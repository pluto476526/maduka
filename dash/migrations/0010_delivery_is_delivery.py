# Generated by Django 5.1.3 on 2025-03-26 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_transaction_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='is_delivery',
            field=models.BooleanField(default=True),
        ),
    ]
