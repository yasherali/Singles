# Generated by Django 4.2 on 2024-04-01 06:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('user_management', '0033_delete_adminuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='admin_user', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='email address')),
                ('password', models.CharField(max_length=128, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'admin_user',
            },
        ),
    ]
