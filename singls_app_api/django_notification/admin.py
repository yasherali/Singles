from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(Notification)
class Notification(admin.ModelAdmin):
    list_display = ["notification","sender_profile","reciever_profile"]

@admin.register(AdminNotification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["sender_id","created_on"]

@admin.register(AdminNotificationMapping)
class AdminNotificationMap(admin.ModelAdmin):
    list_display = ["admin_noti_id", "notification_id"]

@admin.register(NotificationType)
class NotificationType(admin.ModelAdmin):
    list_display = ["type_name", "title", "message", "content"]