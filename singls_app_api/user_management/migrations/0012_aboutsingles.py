# Generated by Django 4.2 on 2024-03-21 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0011_alter_profile_main_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutSingles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('introduction', models.TextField(max_length=256, null=True)),
                ('description', models.TextField(max_length=512, null=True)),
            ],
            options={
                'db_table': 'about_singles',
            },
        ),
    ]
