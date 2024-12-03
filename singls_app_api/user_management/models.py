import random
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime ,date
from django.conf import settings
import os
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser

def save_profile_image(instance, filename):
    file_extension = os.path.splitext(filename)[1].lstrip('.')
    current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
    target_dir = f'profile_images/{instance.user.pk}'
    file_dir = os.path.join(settings.MEDIA_ROOT, target_dir)
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir, 0o777)
    return os.path.join(target_dir, f'{current_datetime}.{file_extension}')

#class AdminUser(AbstractUser):
#    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)

#    USERNAME_FIELD = 'email'
#    REQUIRED_FIELDS = []

#    def __str__(self):
#        return self.email

#    class Meta:
#        db_table = 'admin_user'
#        # Define custom related names for groups and permissions
#        permissions = models.ManyToManyField(
#            'auth.Permission',
#            blank=True,
#            related_name='admin_users'
#        )
#        groups = models.ManyToManyField(
#            'auth.Group',
#            blank=True,
#            related_name='admin_users'
#        )

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, default='user')

    def __str__(self):
        return self.name

def get_default_role():
        return Role.objects.get_or_create(name="user")[0]

class Profile(models.Model):

    # user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name = "profile_user")
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name = "profile")
    join_date = models.DateField(default=date.today)
    phone_number = PhoneNumberField(null=True, blank=True)
    name = models.CharField(null = True, max_length=256)
    about = models.TextField(null=True, max_length=256)
    gender = models.TextField(null=True)
    date_of_birth = models.DateTimeField(null=True)
    main_image = models.ImageField(max_length=256, upload_to =save_profile_image, null=True, blank=True)
    height = models.TextField(null=True)
    sample_height = models.TextField(null=True)
    weight = models.TextField(null=True)
    sample_weight = models.TextField(null=True)
    hair_color = models.TextField(null=True)
    eye_color = models.TextField(null=True)
    face_verified = models.BooleanField(null=True, blank=True, default=False)
    is_delete = models.BooleanField(default=False)
    notification = models.BooleanField(default=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, default=get_default_role, null = True)
    #state = models.CharField(blank=True , null = True)
    #country = models.CharField(blank=True , null = True)
    city = models.CharField(null=True)
    active_status = models.BooleanField(null=True, default=True)
    #role_name = models.CharField(null=True, default='User')
    otp = models.IntegerField(null=True, default='000000')
    verify_otp = models.BooleanField(null=True, blank=True, default=False)
    
    def __str__(self):
        return '%s' % self.user.email
    
    def get_main_image(self):
        return self.main_image.url if self.main_image else None
    
    def get_full_name(self):
        return self.name
        
    class Meta:
        db_table = 'profile'


class BlockedUser(models.Model):
    i_profile = models.ForeignKey(Profile,on_delete=models.CASCADE,related_name='i_user_profile')
    i_blocked_profile = models.ForeignKey(Profile,on_delete=models.CASCADE,related_name='i_blocked_profile')
    
    def __str__(self) -> str:
        return "%s blocked ->%s" % (self.i_profile.user.username, self.i_blocked_profile.user.username)
    
    class Meta:
        db_table = 'blocked_user'

class DatingPreference(models.Model):

    i_profile = models.ForeignKey(Profile, on_delete = models.CASCADE)
    preference = models.JSONField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.preference
    class Meta:
        db_table = 'dating_preference'


class Interest(models.Model):

    i_profile = models.ForeignKey(Profile, on_delete = models.CASCADE)
    interests = models.JSONField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.interests
    class Meta:
        db_table = 'interest'


class SkinColor(models.Model):

    i_profile = models.ForeignKey(Profile, on_delete = models.CASCADE)
    color = models.JSONField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.color
    class Meta:
        db_table = 'skin_color'

class UserCoordinates(models.Model):

    i_profile = models.ForeignKey(Profile, on_delete = models.CASCADE)
    map_active = models.BooleanField(null=True, default=False)
    radius = models.CharField(default=5, null=True)
    current_coordinates = models.JSONField(null=True)

    def __str__(self):
        return '%s' % self.current_coordinates
    class Meta:
        db_table = 'user_coordinates'

class UserQuery(models.Model):

    i_profile = models.ForeignKey(Profile, on_delete = models.CASCADE)
    subject = models.TextField(null=True)
    message = models.TextField(null=True)
    
    def __str__(self):
        return '%s' % self.message
    class Meta:
        db_table = 'user_query'

class AboutSingles(models.Model):

    introduction = models.TextField(null=True, max_length=256)
    description = models.TextField(null=True, max_length=512)

    def __str__(self):
        return '%s' % self.description
    class Meta:
        db_table = 'about_singles'

class PrivacyPolicy(models.Model):

    privacypolicy = models.TextField(null=True, max_length=512)

    def __str__(self):
        return '%s' % self.privacypolicy
    class Meta:
        db_table = 'privacy_policy'

class TermsAndConditions(models.Model):

    text = models.TextField(null=True, max_length=512)

    def __str__(self):
        return '%s' % self.text
    class Meta:
        db_table = 'terms_and_conditions'


class StaticContent(models.Model):
    type = models.TextField(null=True)
    title = models.TextField(null=True)
    content = models.TextField(null=True)

    class Meta:
        db_table = 'static_content'

class Reports(models.Model):
    reported_by_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reports_reported_by')
    report_about_message = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reports_report_about')
    claim = models.TextField(null=True)
    content = models.TextField(null=True)
    request = models.TextField(null=True, default='Pending')
    response = models.TextField(null=True)

    class Meta:
        db_table = 'reports'


class FAQ(models.Model):

    question = models.TextField(null=True, max_length=256)
    answer = models.TextField(null=True, max_length=512)

    def __str__(self):
        return '%s' % self.question
    class Meta:
        db_table = 'answer'