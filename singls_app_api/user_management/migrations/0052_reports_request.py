# Generated by Django 4.2 on 2024-04-26 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0051_profile_active_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='reports',
            name='request',
            field=models.TextField(default='Pending', null=True),
        ),
    ]