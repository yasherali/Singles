# Generated by Django 4.2 on 2024-04-01 06:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0030_remove_profile_role_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adminuser',
            old_name='email',
            new_name='username',
        ),
    ]
