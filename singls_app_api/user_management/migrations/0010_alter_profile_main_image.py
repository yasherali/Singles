# Generated by Django 4.2 on 2024-03-19 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0009_remove_datingpreference_female_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='main_image',
            field=models.FileField(blank=True, max_length=256, null=True, upload_to='save_profile_image/images1'),
        ),
    ]
