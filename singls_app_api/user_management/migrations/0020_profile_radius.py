# Generated by Django 4.2 on 2024-03-22 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0019_profile_map_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='radius',
            field=models.CharField(default=5, null=True),
        ),
    ]
