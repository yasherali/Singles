# Generated by Django 4.2 on 2024-04-01 06:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0034_adminuser'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AdminUser',
        ),
    ]
