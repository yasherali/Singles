# Generated by Django 4.2 on 2024-04-19 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0050_remove_profile_active_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='active_status',
            field=models.BooleanField(default=True, null=True),
        ),
    ]
