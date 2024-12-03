# Generated by Django 4.2 on 2024-04-05 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0042_profile_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='verify_otp',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='otp',
            field=models.IntegerField(default='000000', null=True),
        ),
    ]
