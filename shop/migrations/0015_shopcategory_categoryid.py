# Generated by Django 5.1.3 on 2025-04-04 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_rename_bloggpost_blogcomment_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopcategory',
            name='categoryID',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
    ]
