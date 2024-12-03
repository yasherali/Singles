from django.forms import model_to_dict
from django_rest_authentication.authentication.serializers import MainRegisterSerializer, SocialTokenObtainPairSerializer, CustomTokenObtainPairSerializer
from django_rest_authentication.authentication.serializers import (MyTokenObtainPairSerializer,RefreshToken,
                                                                   api_settings,update_last_login, LogoutSerializer)
from rest_framework import serializers
from django_chat.serializers import MessageSerializer
from django_chat.models import Message
from django_notification.serializers import FcmDeviceSerializer
from django_notification.models import *
from rest_framework import status
import magic
from .utils import decode_base64_file, get_model_objects, get_profiles
from user_management.countries import COUNTRY_CHOICES
from .utils import get_user_roles, validate_phone_number
from django.db import transaction
# from django_firestore_messaging.utils import create_firebase_profile_signup,signin_firebase,get_firestore_id
from .models import *
from django.core.files import File
import re
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from fcm_django.models import FCMDevice
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from phonenumber_field.serializerfields import PhoneNumberField
from allauth.socialaccount.models import SocialAccount
from django_rest_authentication.authentication.django_rest_passwordreset.models import ProfileOTP, UserOfOTP
from django_firestore_messaging.utils import signin_firebase
from django_firestore_messaging.models import *
from user_management.utils import get_firestore_id, create_firebase_profile_signup
from subscription.models import Membership

class TokenPairSerializer(CustomTokenObtainPairSerializer):
    pass

class SocialAuthSerializer(SocialTokenObtainPairSerializer):

    def get_age(self, dob):
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        else:
            return None
    
    def validate(self, attrs):
        validate_data = super().validate(attrs).copy()
        attrs['valid'] = False
        
        if validate_data['valid']:
            if validate_data['login'] == False:
                attrs['profile_creation'] = True
            else:
                attrs['profile_creation'] = False
                
            attrs['valid'] = True   
        
        return attrs
    def create(self, validated_data):
        create_data = super().create(validated_data)
        firestore_token = None
        
        if validated_data['valid'] and not create_data['message'] in ['Full name is required', 'Email is required']:
            user_id = create_data['data']['pk']
            try:
                # Check if a profile already exists for the user
                profile = Profile.objects.get(user_id=user_id)
            except Profile.DoesNotExist:
                # If profile does not exist, create a new profile
                profile = Profile.objects.create(user_id=user_id, name=validated_data.get('full_name', ''))

            try:
                interests = Interest.objects.get(i_profile__user_id=user_id)
                profile_done = True
            except Interest.DoesNotExist:
                interests = None
                profile_done = False

            try:
                preferences = DatingPreference.objects.get(i_profile=profile)
            except DatingPreference.DoesNotExist:
                preferences = None

            try:
                skin_colors = SkinColor.objects.get(i_profile=profile)
            except SkinColor.DoesNotExist:
                skin_colors = None
            
            try:
                map_active = UserCoordinates.objects.get(i_profile=profile)
                map_active = map_active.map_active
            except UserCoordinates.DoesNotExist:
                map_active = False
            
            try:
                is_subscribed = Membership.objects.get(i_profile__user_id = user_id, is_active = True).is_active
            except Membership.DoesNotExist:
                is_subscribed = False


            
            print(profile, "=================")
            firestore_token = create_firebase_profile_signup(profile)
            firestore_id = get_firestore_id(profile)
            print(firestore_id, "--------")
            create_data['data']['firebase_id'] = firestore_id

            try:
                social_account = SocialAccount.objects.get(user=profile.user)
                uid = social_account.uid
            except SocialAccount.DoesNotExist:
                uid = None

            try:
                active_status = profile.active_status
            except Profile.DoesNotExist:
                active_status = False

            if not active_status:
                return {
                    "data": {},
                    "message": "Your account has been deactivated by the admin.",
                    "status": False,
                    "status_code": status.HTTP_403_FORBIDDEN
                }
            
            if profile_done:
                age = self.get_age(profile.date_of_birth)
                main_image = profile.main_image.url if profile.main_image else None
                
                # Get the group_id associated with the user's profile
                private_group = PrivateGroupMapp.objects.filter(i_profile=profile).first()
                if private_group:
                    group_detail = private_group.i_group
                    group_detail.group_image = main_image
                    group_detail.save()

            create_data['data'].update({
                'firebase_id': firestore_id,
                'social': True,
                'is_new_user': validated_data['login'],
                'profile_done': profile_done,
                'firebase_token': firestore_token,
                'uid': uid,
                'is_subscribed' : is_subscribed,
                'active_status' : active_status,
                'name': profile.name if profile_done else None,
                'age': age if profile_done else None,
                'main_image': main_image if profile_done else None,
                'height': profile.height if profile_done else None,
                'weight': profile.weight if profile_done else None,
                'hair_color': profile.hair_color if profile_done else None,
                'eye_color': profile.eye_color if profile_done else None,
                'interest': interests.interests if interests else None,
                'preference': preferences.preference if preferences else None,
                'skin_color': skin_colors.color if skin_colors else None,
                'map_active': map_active
            })
            
            unwanted_keys = ['password', 'last_login', 'is_superuser', 'is_staff', 'date_joined']
            return_data = {key: value for key, value in create_data.items() if key not in unwanted_keys}
            self.resp = {
                'data': return_data['data'],
                'message': create_data['message'],
                'status': create_data['status'],
                'status_code': create_data['status_code']
            }
        else:
            # If validation fails or user creation fails, return appropriate response
            self.resp = {
                "data": {},
                "message": create_data['message'] if 'message' in create_data else validated_data['message'],
                "status": False,
                "status_code": status.HTTP_400_BAD_REQUEST
            }

        return self.resp
    
class SingleMessageSerializer(MessageSerializer):
    class Meta:
        model = Message
        fields = ['sender', 'reciepient', 'message', 'chat_media', 'type']

class GetMessagesSerializer(serializers.Serializer):
    reciepient = serializers.IntegerField()
    
class aboutnameserializer(serializers.Serializer):
    class Meta:
        model = Profile
        fields = ['name', 'about']

    #def create(self, validated_data):
    #    return Profile.objects.create(**validated_data)
    
    #def update(self, instance, validated_data):
    #    instance.name = validated_data.get('name', instance.name)
    #    instance.about = validated_data.get('about', instance.about)
    #    instance.save()
    #    return instance
    
class profileserializer(serializers.Serializer):
    name = serializers.CharField()
    about = serializers.CharField()

    def validate(self, data):
        name = data.get('name')
        about = data.get('about')

        if not re.match("^[a-zA-Z\s]+$", name):
            raise serializers.ValidationError("Name must only contain letters and spaces.")
        if not re.match("^[a-zA-Z\s\d\W]+$", about):
            raise serializers.ValidationError("About must only contain letters, spaces, digits, and special characters.")

        return data

class phonenumberotpserializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    otp = serializers.IntegerField(required=True)

class genderserializer(serializers.Serializer):
    gender = serializers.CharField(max_length=50)

    def validate_gender(self, value):
        if not re.match("^(male|female|lgbtq)$", value.lower()):
            raise serializers.ValidationError("Gender must be 'male', 'female', or 'lgbtq'.")
        return value


class profilepicserializer(serializers.Serializer):
    class Meta:
        model = Profile
        fields = ['main_image']

class dobserializer(serializers.Serializer):
    date_of_birth = serializers.DateTimeField()

    def validate_date_of_birth(self, value):
        # Check if date of birth is in the future
        if value > timezone.now():
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        # Check if the provided date is not in UTC
        if timezone.is_naive(value):
            raise serializers.ValidationError("Date of birth must be in UTC.")

        return value
    
class heightserializer(serializers.Serializer):
    height = serializers.CharField(max_length=50)
    sample = serializers.CharField(max_length=50)

class weightserializer(serializers.Serializer):
    weight = serializers.CharField(max_length=50)
    sample = serializers.CharField(max_length=50)

class hairserializer(serializers.Serializer):
    hair_color = serializers.CharField(max_length=50)

class eyeserializer(serializers.Serializer):
    eye_color = serializers.CharField(max_length=50)

class skinserializer(serializers.Serializer):
    color = serializers.CharField(max_length=50)

    def update(self, instance, validated_data):
        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance

class datingserializer(serializers.Serializer):
    preference = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False
    )

    def validate_preference(self, value):

        valid_preferences = ["Male", "Female", "LGBTQ", "male", "female", "lgbtq"]
        for pref in value:
            if pref not in valid_preferences:
                raise serializers.ValidationError("Invalid preference: {}".format(pref))
        return value

    def create(self, validated_data):
        return DatingPreference.objects.create(preference=validated_data['preference'])
    
    def update(self, instance, validated_data):
        instance.preference = [pref.lower() for pref in validated_data.get('preference', instance.preference)]
        instance.save()
        return instance

class interestserializer(serializers.Serializer):
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),  
        allow_empty=False  
    )

    def validate_interest(self, value):
        valid_interest = ["art & design", "beauty", "food", "diy & food", "music", "gaming", "Finance & business", "health & lifestyle", "relationship", "travel & nature", "sports", "fashion", "animals", "technology", "reading & literature", "entertainment", "diy & home"]  
        for pref in value:
            if pref not in valid_interest:
                raise serializers.ValidationError("Invalid Interest: {}".format(pref))
        return value

    def create(self, validated_data):
        return Interest.objects.create(interests=validated_data['interests'])
    
    def update(self, instance, validated_data):
        instance.interests = validated_data.get('interests', instance.interests)
        instance.save()
        return instance


class faceverifyserializer(serializers.Serializer):
    face_verified = serializers.BooleanField()

class notificationserializer(serializers.Serializer):
    notification = serializers.BooleanField()

class mapactiveserializer(serializers.Serializer):
    map_active = serializers.BooleanField()
    #current_location = serializers.CharField(max_length=256)
    current_coordinates = serializers.JSONField()

class MainImageUpdateSerializer(serializers.Serializer):
    main_image = serializers.CharField(required=True)

    def validate_main_image(self, value):
        try:
            decoded_image = base64.b64decode(value)
        except Exception as e:
            raise serializers.ValidationError("Invalid base64 data")
        return decoded_image

class aboutsingleserializer(serializers.Serializer):
    introduction = serializers.CharField(max_length=256)
    description = serializers.CharField(max_length=512)

    def create(self, validated_data):
        return AboutSingles.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.introduction = validated_data.get('introduction', instance.introduction)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
class privacypolicyserializer(serializers.Serializer):
    privacypolicy = serializers.CharField(max_length=512)

    def create(self, validated_data):
        return PrivacyPolicy.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.privacypolicy = validated_data.get('privacypolicy', instance.privacypolicy)
        instance.save()
        return instance

class termsconditionsserializer(serializers.Serializer):
    text = serializers.CharField(max_length=512)

    def create(self, validated_data):
        return TermsAndConditions.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance
    
class SignoutSerializer(LogoutSerializer):
    pass

class AdminSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')

        # Check if both email and password are provided
        if email and password:
            #admin_user = AdminUser.objects.create(email=email, password=password)
            pass
            #return admin_user
        else:
            # If email or password is missing, raise a validation error
            raise serializers.ValidationError("Email and password are required.")

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['pk', 'name', 'email', 'phone_number', 'role']

    def get_email(self, obj):
        return obj.user.email
    
    def get_role(self, obj):
        return obj.role.name

class UserActiveDeactiveSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    is_active = serializers.BooleanField()

    def validate_is_active(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("is_active must be a boolean value.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'is_active' in data:
            # Convert boolean value to strings 'active' or 'inactive'
            data['is_active'] = 'active' if data['is_active'] else 'inactive'
        return data
    
class UserQuerySerializer(serializers.ModelSerializer):
    subject = serializers.CharField(max_length=256)
    message = serializers.CharField(max_length=256)

    class Meta:
        model = UserQuery
        fields = ['subject', 'message']

class GetQuerySerializer(serializers.Serializer):
    class Meta:
        model = UserQuery
        fields = ['message']


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['registration_id', 'type', 'user_id']

    def create(self, validated_data):
        registration_id = validated_data.get('registration_id')
        device_type = validated_data.get('type')
        user_id = validated_data.get('user_id')

        # Check if a device with the provided user_id already exists
        existing_device = FCMDevice.objects.filter(user_id=user_id).first()

        if existing_device:
            # Update the existing device's details
            existing_device.registration_id = registration_id
            existing_device.type = device_type
            existing_device.save()
            # Set a flag to indicate that an existing device was updated
            setattr(existing_device, '_update_existing', True)
            return existing_device
        else:
            # Create a new device
            return FCMDevice.objects.create(registration_id=registration_id, type=device_type, user_id=user_id)

    
class FAQSerializer(serializers.ModelSerializer):

    class Meta:
        model = FAQ
        fields = '__all__'

    def create(self, validated_data):
        return FAQ.objects.create(**validated_data)

class BlockedProfileSerializer(serializers.Serializer):
    status = serializers.BooleanField(read_only=True)
    data = serializers.DictField(read_only=True,default = {})
    status_code = serializers.IntegerField(read_only = True)
    message = serializers.CharField(read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resp = {'status' : False}
        request = self.context["request"]
        self.user = request.user
        self.fields["profile_id"] = serializers.IntegerField(write_only=True)
    
    def validate(self, attrs):
        attrs['valid'] = False
        if not attrs ['profile_id']:
            self.resp['message'] = "profile_id is required. "
            self.resp['status_code'] = status.HTTP_400_BAD_REQUEST
        profile_exist = Profile.objects.filter(pk = attrs['profile_id'], is_delete=False).exists()
        if not profile_exist:
            self.resp['message'] = "Profile does't exists. "
            self.resp['status_code'] = status.HTTP_404_NOT_FOUND
        else:
            attrs['valid'] = True

        return attrs
        
    def create(self, validated_data):
        if validated_data['valid'] == True:
            with transaction.atomic():
                blockuserprofile_obj = Profile.objects.get(pk = int(validated_data['profile_id']))
                blockuser_obj = BlockedUser.objects.create(
                    i_profile = self.user.profile,
                    i_blocked_profile = blockuserprofile_obj
                )              
                self.resp["message"] = "Blocked User Profile"
                self.resp["status"] = True
                self.resp['status_code'] = status.HTTP_200_OK
                print("self.resp : ", self.resp)
        return self.resp

class UnBlockedProfileSerializer(serializers.Serializer):
    status = serializers.BooleanField(read_only=True)
    data = serializers.DictField(read_only=True,default = {})
    status_code = serializers.IntegerField(read_only = True)
    message = serializers.CharField(read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resp = {'status': False}
        request = self.context.get("request")
        self.user = request.user if request and hasattr(request, "user") else None
        self.fields["block_id"] = serializers.IntegerField(write_only=True, required=True)

    def validate(self, attrs):
        attrs['valid'] = False
        block_id = attrs.get('block_id')

        if not self.user:
            self.resp['message'] = "Authentication credentials were not provided."
            self.resp['status_code'] = status.HTTP_401_UNAUTHORIZED
            return attrs

        # Check if the block exists and if the user who blocked is the one making the unblock request
        blockeduser_exist = BlockedUser.objects.filter(i_blocked_profile_id=block_id, i_profile=self.user.profile).exists()

        if not blockeduser_exist:
            self.resp['message'] = "Unable to perform. Block does not exist or you are not authorized to unblock."
            self.resp['status_code'] = status.HTTP_400_BAD_REQUEST
        else:
            attrs['valid'] = True

        return attrs

    def create(self, validated_data):
        if validated_data['valid']:
            block_id = validated_data['block_id']
            blockeduser_obj = BlockedUser.objects.get(i_blocked_profile_id=block_id, i_profile=self.user.profile)
            blockeduser_obj.delete()
            self.resp["message"] = "Unblocked user profile"
            self.resp['status_code'] = status.HTTP_200_OK
            self.resp["status"] = True

        return self.resp
    
class StaticContentPostSerializer(serializers.ModelSerializer):
    TYPE_CHOICES = [
        ('terms_and_conditions', 'Terms and Conditions'),
        ('privacy_policy', 'Privacy Policy'),
        ('about', 'About'),
        ('faq', 'FAQ')
    ]
    
    type = serializers.ChoiceField(choices=TYPE_CHOICES)

    class Meta:
        model = StaticContent
        fields = ['type', 'title', 'content']

class ReportsSerializer(serializers.ModelSerializer):
    claim_choices = (
        ('Nudity', 'Nudity'),
        ('Spam', 'Spam'),
        ('False Information', 'False Information'),
        ('Violence', 'Violence'),
        ('Others', 'Others'),
    )

    claim = serializers.ChoiceField(choices=claim_choices)
    content = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    
    class Meta:
        model = Reports
        fields = ['reported_by_profile', 'report_about_message', 'claim', 'content', 'id', 'request', 'response']

class ReportsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reports
        fields = ['id', 'request', 'response']

    def validate_request(self, value):
        if value not in ['Pending', 'Accept', 'Reject']:
            raise serializers.ValidationError("Invalid request value. Must be one of: 'Pending', 'Accept', 'Reject'.")
        return value
    