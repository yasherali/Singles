from django.db import models
from user_management.models import Profile
from django.utils import timezone
# from django.contrib.postgres.fields import JSONField

# Create your models here.
NOTIFICATION_TYPES = (('message', 'message'),('profile', 'profile'),('request', 'request'),('join_group', 'join_group'),('group_request', 'group_request'),('other', 'other'),('post','post'),('comment', 'comment'),('birthday', 'birthday'),('post_request', 'post_request'),('group_invite', 'group_invite'), ('questionire', 'questionire'))

class NotificationType(models.Model):
    type_name = models.CharField(max_length=30, null=False)
    title = models.CharField(max_length=100, null=True, blank=True)
    message = models.CharField(max_length=100, null=True, blank=True)
    content = models.JSONField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.type_name

class AdminNotification(models.Model):
    sender_id = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="admin_noti_profile")
    created_on = models.DateTimeField(default=timezone.now)


class Notification(models.Model):
    reciever_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="noti_reciever_profile", help_text="foreign key of notification reciever user")
    notification = models.TextField(help_text="notification message")
    title = models.CharField(max_length=255, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    sender_profile = models.ForeignKey(Profile, default=None, null=True, blank=True, related_name="noti_sender_profile", on_delete=models.CASCADE, help_text="foreign key of notification sender user")
    created_on = models.DateTimeField(default=timezone.now)
    type = models.ForeignKey(NotificationType, on_delete=models.SET_NULL, related_name='notification_type', null=True, blank=True)
    action = models.BooleanField(default=False)
    content = models.JSONField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.notification
    
    
class AdminNotificationMapping(models.Model):
    admin_noti_id = models.ForeignKey(AdminNotification, on_delete=models.CASCADE, related_name="admin_notification_id")
    notification_id = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="notification_reference")
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return '%s' % self.admin_noti_id