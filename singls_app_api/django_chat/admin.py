from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(ReadBy)
class ReadByAdmin(admin.ModelAdmin):
    list_display = ["message_id","i_profile", "read"]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["message","sender","reciepient","created_at"]

@admin.register(UserActivity)
class PublicGroupAdmin(admin.ModelAdmin):
    list_display = ["i_profile","conn_profile","last_activity"]

@admin.register(MuteMessage)
class MuteMessageAdmin(admin.ModelAdmin):
    list_display = ["i_profile","m_profile"]