# Generated by Django 5.1.3 on 2025-04-05 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_alter_shopcategory_categoryid'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='slug',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
