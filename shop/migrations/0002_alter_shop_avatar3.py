# Generated by Django 5.1.3 on 2025-03-05 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shop',
            name='avatar3',
            field=models.ImageField(default='shop3.jpg', upload_to=''),
        ),
    ]
