# Generated by Django 4.2 on 2024-03-18 10:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='dating_preference',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='interest',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='skin_color',
        ),
    ]
