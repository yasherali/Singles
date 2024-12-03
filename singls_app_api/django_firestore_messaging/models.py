from django.db import models
from django.utils import timezone
import os, random
from datetime import datetime
from django.conf import settings
from user_management.models import Profile

# Create your models here.

def save_group_image(instance, filename):
        file_extension = os.path.splitext(filename)[1].lstrip('.')
        random_number = random.randint(0, 99)
        current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')+str(random_number)+str(random_number)
        target_dir = f'chat_group_file/{datetime.strftime(instance.created_at,"%y-%m-%d")}/{instance.pk}'
        file_dir = os.path.join(settings.MEDIA_ROOT, target_dir)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir, 0o777)
        return os.path.join(target_dir, f'{current_datetime}.{file_extension}')

class GroupDetail(models.Model):
    MSG_TYPE = [('group', 'group'),('private', 'private')]
    group_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=256, choices=MSG_TYPE, default='private')
    group_image = models.FileField(max_length=256, upload_to = save_group_image, null=True, blank=True)
    def __str__(self):
        return '%s' % self.group_name
    
    
    def get_group_name(self):
        group_name = None
        if self.type=='private':
            profile = Profile.objects.filter(pk=self.created_by).first()
            group_name = profile.get_full_name()
        elif self.type=='group':
            group_name = self.group_name

        return group_name
    
    def get_group_image(self):
        group_pic = None
        if self.type=='private':
            profile = Profile.objects.filter(pk=self.created_by).first()
            group_pic = profile.get_main_image()
        elif self.type=='group':
            try:
                main_index = self.group_image.path.split("/").index('media')
                group_pic =  "/".join(self.group_image.path.split("/")[main_index:])
            except Exception: pass
        return group_pic

    class Meta:
        db_table = 'group_detail'

class FirestoreGroupMapp(models.Model):
    i_group = models.ForeignKey(GroupDetail, on_delete=models.CASCADE, related_name="firegroupdetail")
    firestore_id = models.CharField(max_length=255)

    def __str__(self):
        return '%s' % self.firestore_id
    
    class Meta:
        db_table = 'firestore_mapping'

class PrivateGroupMapp(models.Model):
    i_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="profile")
    i_group = models.ForeignKey(GroupDetail, on_delete=models.CASCADE, related_name="profile_group")

    def __str__(self):
        return '%s' %self.i_group.group_name
        
    class Meta:
        db_table = 'private_mapping'

class PublicGroupMapp(models.Model):
    i_profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    i_group = models.ForeignKey(GroupDetail, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s' %self.i_group.group_name
    
    class Meta:
        db_table = 'public_mapping'
    
