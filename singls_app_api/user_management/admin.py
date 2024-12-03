from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'name' ,'date_of_birth' ,'main_image', 'is_delete']

@admin.register(DatingPreference)
class DatingPreferenceAdmin(admin.ModelAdmin):
    list_display = ['i_profile', 'preference']

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['i_profile', 'interests']

@admin.register(SkinColor)
class SkinColorAdmin(admin.ModelAdmin):
    list_display = ['i_profile', 'color']

@admin.register(UserCoordinates)
class UserCoordinatesAdmin(admin.ModelAdmin):
    list_display = ['i_profile', 'map_active', 'current_coordinates']

@admin.register(UserQuery)
class UserQuerysAdmin(admin.ModelAdmin):
    list_display = ['i_profile', 'subject', 'message']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Reports)
class ReportsAdmin(admin.ModelAdmin):
    list_display = ['reported_by_profile', 'claim', 'content']

@admin.register(StaticContent)
class StaticContentAdmin(admin.ModelAdmin):
    list_display = ['type', 'title', 'content']