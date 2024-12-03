from django.db import models
from user_management.models import Profile
from django.utils import timezone
import os, random
from django_firestore_messaging.models import *
from datetime import datetime

# Create your models here.

def save_chat_file(instance, filename):
        file_extension = os.path.splitext(filename)[1].lstrip('.')
        random_number = random.randint(0, 99)
        current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')+str(random_number)+str(random_number)
        target_dir = f'chat_file/{datetime.strftime(instance.created_at,"%y-%m-%d")}/{instance.sender}'
        file_dir = os.path.join(settings.MEDIA_ROOT, target_dir)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir, 0o777)
        return os.path.join(target_dir, f'{current_datetime}.{file_extension}')

class Message(models.Model):
    MSG_TYPE = [('group', 'group'),('private', 'private')]
    message = models.TextField(null=True, blank=True)
    sender = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="message_sender")
    reciepient = models.ForeignKey(Profile, on_delete=models.SET_NULL, related_name="message_reciever", null=True, blank=True)
    chat_media = models.FileField(max_length=256, upload_to = save_chat_file, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=256, choices=MSG_TYPE)
    i_group = models.ForeignKey(GroupDetail, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.CharField(max_length=100, default='en')
    ############ Below fields added for Vifty Reel share in Chat #########################
    reel_id = models.IntegerField(null = True, blank = True)
    video_type = models.CharField(max_length = 250, null = True, blank = True)
    media = models.BooleanField(default = False)

    def __str__(self):
        return '%s' %self.message
    
    def get_message_status(self):
        try:
            obj = ReadBy.objects.get(message_id__pk = self.pk)
            resp = obj.read
        except Exception :
            resp = True
        return resp
    
    
    class Meta:
        db_table = 'message_mapping'


class ReadBy(models.Model):
    message_id = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_seen")
    read = models.BooleanField(default=False)
    i_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='read_profile')

    def __str__(self):
        return '%s' %self.message_id
    
    class Meta:
        db_table = 'read_by'

class UserActivity(models.Model):
    i_profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='active_profile')
    last_activity = models.DateTimeField(default=timezone.now)
    conn_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='conn_profile')

    def __str__(self):
        return '%s' %self.i_profile.get_full_name()
    
    class Meta:
        db_table = "user_activity"

class MuteMessage(models.Model):
    i_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="mute_profile")
    m_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="m_profile")
    creater_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s' %self.i_profile.get_full_name()
    
    class Meta:
        db_table = "mute_message"


