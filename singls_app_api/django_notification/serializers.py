from rest_framework import serializers
from .models import *
from fcm_django.models import FCMDevice
from user_management.models import Profile
from django.contrib.auth.models import User
from datetime import datetime , timedelta
from rest_framework import status
import timeit

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name']
        
class ProfileSerializer(serializers.ModelSerializer):
    # user = UserSerializer()

    class Meta:
        model = Profile
        fields = ['pk', 'main_image']

class NotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationType
        fields = ['type_name']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationSerializerView(serializers.ModelSerializer):
    sender_profile = ProfileSerializer(read_only=True)  # Use the ProfileSerializer for non-null sender_profiles
    created_on = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if sender_profile is None and customize representation
        if representation['sender_profile'] is None:
            representation['sender_profile'] = {
                'pk': None,
                'main_image': None
            }

        return representation

        
    def get_created_on(self, obj):
        timestamp = datetime.fromisoformat(datetime.strftime(obj.created_on,"%Y-%m-%dT%H:%M:%S"))
        now = datetime.now()
        delta = now - timestamp
        if delta < timedelta(days=1):
            seconds = delta.seconds
            minutes = seconds // 60
            hours = minutes // 60
            if hours > 0:
                return f"{hours} hrs"
            elif minutes > 0:
                return f"{minutes} mins"
            else:
                return f"{seconds} secs"
        # elif delta < timedelta(days=7):
        #     return f"{delta.days} days ago"
        # elif delta < timedelta(weeks=4):
        #     weeks = delta.days // 7
        #     return f"{weeks} weeks ago"
        # elif delta < timedelta(days=365):
        #     return timestamp.strftime("%b-%d")
        else:
            return timestamp.strftime("%b-%d-%Y %I:%M %p")
        
    def get_type(self, obj):
        if obj.type is None:
            return None
        return obj.type.type_name  # Extract the type_name value

class FcmDeviceSerializer(serializers.Serializer):
    class Meta:
        model = FCMDevice
        fields = '__all__'

class AdminNotificationSerializerView(serializers.ModelSerializer):
    sender_id = ProfileSerializer()
    # reciever_profile = ProfileSerializer()
    class Meta:
        model = AdminNotification
        fields = '__all__'


class AdminNotificationCreate(serializers.Serializer):
    status_code = serializers.IntegerField(read_only = True)
    data = serializers.DictField(read_only=True,default = None)
    status = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context["request"]
        self.request = request
        self.resp = {'status' : False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': None, 'data':{}}
        self.fields['title'] = serializers.CharField(write_only=True, required=True)
        self.fields['notification'] = serializers.CharField(write_only=True, required=True)

    
    def validate(self, attrs):
        attrs['valid'] = False

        if "title" not in attrs or attrs['title'] is None:
            self.resp["message"] = "Title is required field."

        elif "notification" not in attrs or attrs['notification'] is None:
            self.resp["message"] = "Message is required field."
        
        else:
            attrs['valid'] = True

        return attrs
    
    def get_attribute(self, instance):
        
        return super().get_attribute(instance)
    
    def create(self, validated_data):
        if validated_data['valid'] == True:
            start_time = timeit.default_timer()  # Start measuring the overall execution time
            from .utils import create_all_usernotification
            headers = create_all_usernotification(self.request, validated_data["notification"], validated_data["title"])
            execution_time = timeit.default_timer() - start_time  # Calculate the overall execution time
            print(f"Overall execution time: {execution_time} seconds")
            print("===================================================")
            self.resp["status"] = True
            self.resp["message"] = "Notification send to all users"
            self.resp["status_code"]= status.HTTP_201_CREATED
            # response_data = {"status": True, "status_code": status.HTTP_201_CREATED, "message": "Notification send to all users", "data": ""}
        return self.resp