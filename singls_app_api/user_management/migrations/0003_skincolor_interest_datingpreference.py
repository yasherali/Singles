# Generated by Django 4.2 on 2024-03-18 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0002_remove_profile_dating_preference_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SkinColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.JSONField(blank=True, null=True)),
                ('i_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_management.profile')),
            ],
            options={
                'db_table': 'skin_color',
            },
        ),
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interests', models.JSONField(blank=True, null=True)),
                ('i_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_management.profile')),
            ],
            options={
                'db_table': 'interest',
            },
        ),
        migrations.CreateModel(
            name='DatingPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference', models.JSONField(blank=True, null=True)),
                ('i_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_management.profile')),
            ],
            options={
                'db_table': 'dating_preference',
            },
        ),
    ]