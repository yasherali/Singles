from rest_framework import serializers
from rest_framework import status
from .models import *
from firebase_admin import auth
from .utils import create_firebase_profile

class CreateFirebaseUid(serializers.Serializer):
    status_code = serializers.IntegerField(read_only = True)
    data = serializers.DictField(read_only=True,default = None)
    status = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context["request"]
        self.user = request.user
        self.resp = {'status' : False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': None, 'data':{}}
        
    def validate(self, attrs):
        attrs['valid'] = True

        return super().validate(attrs)
    
    def create(self, validated_data):
        if validated_data['valid']==True:
            uid = str(self.user.profile.pk)
            # Create a custom token
            custom_token = auth.create_custom_token(uid)
            try:
                firestore_id = FirestoreGroupMapp.objects.get(i_group__created_by = self.user.profile).firestore_id
            except:
                return {"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "firestore group not found", "data":''}

            resp = {'status': True, "status_code": status.HTTP_200_OK, "message": "", "data": {'token': custom_token.decode('ASCII'), 'firestore_id': firestore_id}}
        return resp
    

class CreateFirebaseGroup(serializers.Serializer):
    status_code = serializers.IntegerField(read_only = True)
    data = serializers.DictField(read_only=True,default = None)
    status = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context["request"]
        self.user = request.user
        self.resp = {'status' : False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': None, 'data':{}}

    def validate(self, attrs):
        attrs['valid'] = True

        return super().validate(attrs)
    

    def create(self, validated_data):
        if validated_data['valid']==True:
            profile_id = Profile.objects.get(pk=self.user.profile)
            ret = create_firebase_profile(profile_id)
        return ret