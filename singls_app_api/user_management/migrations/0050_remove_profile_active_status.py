# Generated by Django 4.2 on 2024-04-19 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0049_reports'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='active_status',
        ),
    ]
