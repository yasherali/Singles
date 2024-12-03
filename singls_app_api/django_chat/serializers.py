from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User


class AddGroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicGroupMapp
        fields = "__all__"

class UserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['pk', 'name']
    
    def get_name(self, obj):
    # Remove the leading slash from main_image name
        profile = Profile.objects.get(pk=obj)
        name = profile.get_full_name()
        return name

class GroupDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDetail
        fields = "__all__"

class GroupMessageSerializer(serializers.ModelSerializer):
    # sender = UserListSerializer()
    class Meta:
        model = Message
        fields = '__all__'
        

class MessageSerializer(serializers.ModelSerializer):
    # sender = UserListSerializer()
    class Meta:
        model = Message
        fields = '__all__'

# class SeenBySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = read_by
#         fields = '__all__'
