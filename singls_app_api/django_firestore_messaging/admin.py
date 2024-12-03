from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(GroupDetail)
class GroupDetailAdmin(admin.ModelAdmin):
    list_display = ["group_name","created_by"]

@admin.register(FirestoreGroupMapp)
class FirestoreAdmin(admin.ModelAdmin):
    list_display = ["i_group","firestore_id"]

@admin.register(PrivateGroupMapp)
class PrivateGroupAdmin(admin.ModelAdmin):
    list_display = ["i_group","i_profile"]

@admin.register(PublicGroupMapp)
class PublicGroupAdmin(admin.ModelAdmin):
    list_display = ["i_group","i_profile"]