# Generated by Django 5.1.3 on 2025-03-31 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_remove_todaysdeal_duration_todaysdeal_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todaysdeal',
            name='category',
        ),
    ]
