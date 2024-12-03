from django.shortcuts import render
from rest_framework.views import APIView
# from user_management.admin import PrivacyAndPolicyAdmin
from django_rest_authentication.dj_rest_auth.views import PasswordChangeView
from user_management import permissions
from rest_framework.permissions import IsAuthenticated
from django_rest_authentication.authentication.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
# from .serializers import UserCustomTokenObtainPairSerializer
from user_management.models import *
from rest_framework.response import Response
from django.forms.models import model_to_dict
from rest_framework import generics, permissions, status
from user_management.permissions import IsUser, IsAdmin
from user_management.serializers import *
from rest_framework.permissions import AllowAny
from user_management.utils import *
from user_management.utils import personalmessage, groupmessage
from django_rest_authentication.authentication.views import UserRegisterView
from django_notification.serializers import *
from django_notification.models import *
#from django_notification.utils import create_all_usernotification, notification_count_api
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveAPIView,ListAPIView
import base64
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from geopy import distance
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from django_rest_authentication.authentication.django_rest_passwordreset.views import generate_otp
from django_rest_authentication.authentication.models import *
from django_firestore_messaging.models import *
from django_notification.serializers import *
from django_notification.views import *
from allauth.socialaccount.models import SocialAccount
from django_chat.views import *
from django_chat.models import *
import geopy.distance
import os
import re
import math
import json
import timeit
from django.core.serializers import serialize
from datetime import datetime
from django.utils import timezone
from rest_framework import serializers

# Create your views here.

class SocialAuthenticationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SocialAuthSerializer

class NameAboutView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = profileserializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data.get('name')
            about = serializer.validated_data.get('about')

            profile.name = name
            profile.about = about
            profile.save()

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Name and About posted successfully.", "data": {'name': name, 'about': about}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PhoneNumberOTPAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        serializer = phonenumberotpserializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            profile = request.user.profile
            profile.phone_number = phone_number
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Phone Number posted successfully.", "data": {'phone_number': phone_number}}, status=status.HTTP_200_OK)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Validation error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class OTPVerificationAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        if 'verify_otp' in request.data:
            verify_otp = request.data['verify_otp']
            profile = request.user.profile
            profile.verify_otp = verify_otp
            profile.save()
            
            return Response(
                {"status": True, "status_code": status.HTTP_200_OK, "message": "OTP verification status updated successfully.", "data": {'verify_otp': profile.verify_otp}}, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Missing 'verify_otp' field in request body."},
                status=status.HTTP_400_BAD_REQUEST
            )

class MainImageView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        serializer = MainImageUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                profile = Profile.objects.get(user=request.user)
            except Profile.DoesNotExist:
                return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

            main_image_data = serializer.validated_data['main_image']

            image_file = ContentFile(main_image_data, name='main_image.jpg')  # Assuming it's a JPEG image

            profile.main_image = image_file
            profile.save()

            image_path = profile.main_image.url if profile.main_image else None
            response_data = {'image_path': image_path}
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Main image updated successfully.", "data": response_data}, status=status.HTTP_200_OK)
        else:
            #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Validation error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class GenderAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = genderserializer(data=request.data)
        if serializer.is_valid():
            profile.gender = serializer.validated_data['gender']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Gender posted successfully.", "data": {'gender': profile.gender}}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        if 'main_image' not in request.data:
            return Response({'error': 'Main image field is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image_data = base64.b64decode(request.data['main_image'])
        except Exception as e:
            return Response({'error': 'Invalid base64 data'}, status=status.HTTP_400_BAD_REQUEST)

        image_file = ContentFile(image_data, name='main_image.jpg')  # Assuming it's a JPEG image

        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        profile.main_image = image_file
        profile.save()

        image_path = profile.main_image.url if profile.main_image else None
        response_data = {'image_path': image_path}
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Image posted successfully.", "data": {'image': response_data}}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def get_image(request, folder, filename):
    base_directory = os.path.join(settings.MEDIA_ROOT, 'save_profile_image')
    image_path = os.path.join(base_directory, folder, filename)
    if not os.path.exists(image_path):
        return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
    return FileResponse(open(image_path, 'rb'), content_type='image/jpg')

@api_view(['GET'])
@permission_classes([AllowAny])
def get_chat_image(request, date_folder, email_folder, filename):
    base_directory = os.path.join(settings.MEDIA_ROOT, 'chat_file')
    image_path = os.path.join(base_directory, date_folder, email_folder, filename)
    
    if not os.path.exists(image_path):
        return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return FileResponse(open(image_path, 'rb'), content_type='image/jpeg')

class DOBAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = dobserializer(data=request.data)
        if serializer.is_valid():
            profile.date_of_birth = serializer.validated_data['date_of_birth']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Date of birth posted successfully.", "data": {'date_of_birth': profile.date_of_birth}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class HeightAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = heightserializer(data=request.data)
        if serializer.is_valid():
            profile.height = serializer.validated_data['height']
            profile.sample_height = serializer.validated_data['sample']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "height posted successfully.", "data": {'height': profile.height, 'sample': profile.sample_height}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class WeightAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = weightserializer(data=request.data)
        if serializer.is_valid():
            profile.weight = serializer.validated_data['weight']
            profile.sample_weight = serializer.validated_data['sample']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "weight posted successfully.", "data": {'weight': profile.weight, 'sample': profile.sample_weight}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class HairColorAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = hairserializer(data=request.data)
        if serializer.is_valid():
            profile.hair_color = serializer.validated_data['hair_color']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "hair color posted successfully.", "data": {'hair_color': profile.hair_color}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class EyeColorAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = eyeserializer(data=request.data)
        if serializer.is_valid():
            profile.eye_color = serializer.validated_data['eye_color']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "eye color posted successfully.", "data": {'eye_color': profile.eye_color}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class FaceVerifyAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = faceverifyserializer(data=request.data)
        if serializer.is_valid():
            profile.face_verified = serializer.validated_data['face_verified']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "face verified posted successfully.", "data": {'face_verified': profile.face_verified}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class DatingPreferenceAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        serializer = datingserializer(data=request.data)
        if serializer.is_valid():
            preference = serializer.validated_data['preference']
            profile = request.user.profile

            # Check if a dating preference entry exists for the profile
            try:
                dating_preference = DatingPreference.objects.get(i_profile=profile)
                dating_preference.preference = preference
                print(preference)
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Dating preference updated successfully.", "data": {'preference': preference}}, status=status.HTTP_200_OK)
            except DatingPreference.DoesNotExist:
                # Create a new dating preference entry
                DatingPreference.objects.create(i_profile=profile, preference=preference)
                print(preference)
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Dating preference posted successfully.", "data": {'preference': preference}}, status=status.HTTP_200_OK)
        else:
            errors = dict(serializer.errors.items())
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Errors", "data": errors}, status=status.HTTP_400_BAD_REQUEST)
        
class SkinColorAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        serializer = skinserializer(data=request.data)
        if serializer.is_valid():
            color = serializer.validated_data['color']
            # Check if a SkinColor instance already exists for the user's profile
            try:
                skin_color = SkinColor.objects.get(i_profile=request.user.profile)
                skin_color.color = color
                skin_color.save()
            except SkinColor.DoesNotExist:
                skin_color = SkinColor.objects.create(i_profile=request.user.profile, color=color)

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "skin color posted successfully.", "data": {'color': color}}, status=status.HTTP_200_OK)
        else:
            # Convert serializer.errors to a regular dictionary
            errors = dict(serializer.errors.items())
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "data": errors}, status=status.HTTP_400_BAD_REQUEST)
class InterestAPIView(APIView):
    permission_classes = [IsUser]

    def get_age(self, dob):
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        else:
            return None

    def post(self, request, format=None):
        serializer = interestserializer(data=request.data)
        if serializer.is_valid():
            interests = serializer.validated_data['interests']
            user_profile = request.user.profile
            try:
                social_account = SocialAccount.objects.get(user=user_profile.user)
                uid = social_account.uid
            except SocialAccount.DoesNotExist:
                uid = None
            
            try:
                interest = Interest.objects.get(i_profile=request.user.profile)
                interest.interests = interests
                interest.save()
            except Interest.DoesNotExist:
                interest = Interest.objects.create(i_profile=request.user.profile, interests=interests)

            try:
                private_mapping = PrivateGroupMapp.objects.get(i_profile_id=user_profile.pk)
                group_id = private_mapping.i_group
                firestore_mapping = FirestoreGroupMapp.objects.get(i_group_id=group_id)
                firestore_id = firestore_mapping.firestore_id
            except (PrivateGroupMapp.DoesNotExist, FirestoreGroupMapp.DoesNotExist):
                firestore_id = None  

            response_data = {
                "pk": user_profile.user_id,
                "name": user_profile.name,
                "email": request.user.email,
                "age": self.get_age(user_profile.date_of_birth),
                "main_image": user_profile.get_main_image(),
                "uid": uid,
                "firestore_id": firestore_id,
                "profile_done": True,
                "is_new_user": True,
            }

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "interest posted successfully.", "data": response_data}, status=status.HTTP_200_OK)
        else:
            # Convert serializer.errors to a regular dictionary
            errors = dict(serializer.errors.items())
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "data": errors}, status=status.HTTP_400_BAD_REQUEST)
        
class UserProfileAPIView(APIView):
    permission_classes = [IsUser]

    def get_age(self, dob):
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age

    def get(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            
            # ============================================
            dating_preference = DatingPreference.objects.get(i_profile=profile)
            dating_preference_serializer = datingserializer(dating_preference)

            # ============================================
            interests = Interest.objects.get(i_profile=profile)
            interests_serializer = interestserializer(interests)

            # ============================================
            skin_color = SkinColor.objects.get(i_profile=profile)
            skin_color_serializer = skinserializer(skin_color)

            # ============================================

            age = self.get_age(profile.date_of_birth)

            response_data = {
                'profile': {
                    'join_date': profile.join_date,
                    'phone_number': str(profile.phone_number),
                    'name': profile.name,
                    'about': profile.about,
                    'age': age,
                    'face_verified': profile.face_verified,
                    'gender': profile.gender,
                    'date_of_birth': profile.date_of_birth,
                    'main_image': profile.main_image.url if profile.main_image.url else None,
                    'height': profile.height,
                    'weight': profile.weight,
                    'hair_color': profile.hair_color,
                    'eye_color': profile.eye_color,
                    'skin_color': skin_color.color,
                    'dating_preference': dating_preference.preference,
                    'interests': interests.interests
                },
            }

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Get Profile", "data": response_data}, status=status.HTTP_200_OK)
        except (Profile.DoesNotExist, DatingPreference.DoesNotExist, Interest.DoesNotExist, SkinColor.DoesNotExist):
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "errors", "errors": 'Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class NameUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            name = request.data.get('name')

            if name is not None:
                if not name:  
                    return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Name must contain only letters.'}, status=status.HTTP_400_BAD_REQUEST)

                profile.name = name
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Name updated successfully.", "data": {'name': profile.name}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Name field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)

class AboutUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            about = request.data.get('about')

            if about is not None:
                # Check if the about text contains only letters and special characters
                if not re.match("^[a-zA-Z\s\d\W]+$", about):
                    return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'About must contain only letters and special characters.'}, status=status.HTTP_400_BAD_REQUEST)

                profile.about = about
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "About updated successfully.", "data": {'about': profile.about}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'About field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class GenderUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            gender = request.data.get('gender')

            if gender is not None:
                profile.gender = gender
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Gender updated successfully.", "data": {'gender': profile.gender}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Gender field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class DOBUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            date_of_birth_str = request.data.get('date_of_birth')

            if date_of_birth_str is not None:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d %H:%M:%S.%fZ')
                if timezone.is_naive(date_of_birth):
                    date_of_birth = timezone.make_aware(date_of_birth, timezone.utc)
                if date_of_birth > timezone.now():
                    return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'date of birth cannot be in future.'}, status=status.HTTP_400_BAD_REQUEST)
                if timezone.is_naive(date_of_birth):
                    return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'date of birth must be in UTC.'}, status=status.HTTP_400_BAD_REQUEST)

                profile.date_of_birth = date_of_birth
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Date of birth updated successfully.", "data": {'date_of_birth': profile.date_of_birth}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Date of birth field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)

class HeightUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            height = request.data.get('height')
            sample_height = request.data.get('sample')

            if height or sample_height is not None:
                profile.height = height
                profile.sample_height = sample_height
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Height updated successfully.", "data": {'height': profile.height, 'sample': profile.sample_height}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Height and sample fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)

class WeightUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            weight = request.data.get('weight')
            sample_weight = request.data.get('sample')

            if weight or sample_weight is not None:
                profile.weight = weight
                profile.sample_weight = sample_weight
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Weight updated successfully.", "data": {'weight': profile.weight, 'sample': profile.sample_weight}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Weight and sample fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class EyeUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            eye_color = request.data.get('eye_color')

            if eye_color is not None:
                profile.eye_color = eye_color
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Eye color updated successfully.", "data": {'eye_color': profile.eye_color}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'eye color field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)

class HairUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            hair_color = request.data.get('hair_color')

            if hair_color is not None:
                profile.hair_color = hair_color
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "hair color updated successfully.", "data": {'hair-color': profile.hair_color}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'hair color field is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'Profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class SkinUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            skin_color_instance, created = SkinColor.objects.get_or_create(i_profile=request.user.profile)

            serializer = skinserializer(instance=skin_color_instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "skin color updated successfully.", "data": {'skin_color': skin_color_instance.color}}, status=status.HTTP_200_OK)
        except SkinColor.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'skin color does not exist'}, status=status.HTTP_400_BAD_REQUEST)

class PreferenceUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            preference_instance, created = DatingPreference.objects.get_or_create(i_profile=request.user.profile)

            serializer = datingserializer(instance=preference_instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "preference updated successfully.", "data": {'preference': preference_instance.preference}}, status=status.HTTP_200_OK)
        except DatingPreference.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'dating preference does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
class InterestUpdateAPIView(APIView):
    permission_classes = [IsUser]

    def put(self, request, format=None):
        try:
            interests_instance, created = Interest.objects.get_or_create(i_profile=request.user.profile)

            serializer = interestserializer(instance=interests_instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "interest updated successfully.", "data": {'interest': interests_instance.interests}}, status=status.HTTP_200_OK)
        except Interest.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "errors": 'dating preference does not exist'}, status=status.HTTP_400_BAD_REQUEST)



class UserNotificationAPIView(APIView):
    permission_classes = [IsUser]

    def get(self, request, format=None):
        try:
            profile = Profile.objects.get(user=request.user)
            response_data = {
                'profile': {
                    'notification': profile.notification
                }    
            }
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Notification status get successfully.", "data": {'notification': profile.notification}}, status=status.HTTP_200_OK)
        except (Profile.DoesNotExist):
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

class NotifyAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Profile does not exist for this user", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = notificationserializer(data=request.data)
        if serializer.is_valid():
            profile.notification = serializer.validated_data['notification']
            profile.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Notification status changed successfully.", "data": {'notification': profile.notification}}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "", "data": {'error': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

class MapActiveAPIView(APIView):
    permission_classes = [IsUser]

    def get_age(self, dob):
        if dob:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        else:
            return None

    def post(self, request, *args, **kwargs):
        user = request.user

        # ============================================
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile does not exist for this user"}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            user_coordinates = UserCoordinates.objects.get(i_profile=profile)
            user_coordinates_exists = True
        except UserCoordinates.DoesNotExist:
            user_coordinates_exists = False

        # ============================================
        serializer = mapactiveserializer(data=request.data)
        if serializer.is_valid():
            map_active = serializer.validated_data['map_active']
            #current_location = serializer.validated_data.get('current_location')
            current_coordinates = serializer.validated_data.get('current_coordinates')

            if user_coordinates_exists:
                user_coordinates.map_active = map_active
                #user_coordinates.current_location = current_location
                user_coordinates.current_coordinates = current_coordinates
                user_coordinates.save()
            else:
                UserCoordinates.objects.create(
                    i_profile=profile,
                    map_active=map_active,
                    #current_location=current_location,
                    current_coordinates=current_coordinates
                )

            # ============================================
            response_data = {}

            if map_active:
                other_users_data = []
                if current_coordinates:
                    active_user_coords = UserCoordinates.objects.filter(map_active=True).exclude(i_profile=profile)
                    blocked_profiles = BlockedUser.objects.filter(i_profile=profile).values_list('i_blocked_profile_id', flat=True)
                    for user_coord in active_user_coords:
                        if user_coord.current_coordinates and user_coord.i_profile.pk not in blocked_profiles:
                            user_current_coordinates = (float(user_coord.current_coordinates['current_lat']), float(user_coord.current_coordinates['current_long']))
                            req_current_coordinates = (float(current_coordinates.get('current_lat')), float(current_coordinates.get('current_long')))
                            distance_in_km = round(distance.distance(user_current_coordinates, req_current_coordinates).km, 2)
                            distance_in_miles = round(distance_in_km * 0.621371, 2)
                            age = self.get_age(user_coord.i_profile.date_of_birth)
                            
                            if distance_in_km <= float(user_coord.radius):
                                interests = Interest.objects.filter(i_profile=user_coord.i_profile).values_list('interests', flat=True).first()
                                group_ids = PrivateGroupMapp.objects.filter(i_profile=user_coord.i_profile).all()
                                group_id_list = [str(group.i_group_id) for group in group_ids]
                                group_id_str = ",".join(group_id_list)
                                
                                other_users_data.append({
                                    'user_id': user_coord.i_profile.pk,
                                    'name': user_coord.i_profile.name,
                                    'main_image': user_coord.i_profile.main_image.url if user_coord.i_profile.main_image else None,
                                    'age': age,
                                    'interest': interests,
                                    'distance': distance_in_miles,
                                    'current_coordinates': user_coord.current_coordinates,
                                    'group_id': group_id_str,
                                })

                response_data["other_users"] = other_users_data
            else:
                response_data["message"] = "Map is inactive. No need to calculate distances."

            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Map Active changed successfully.", "data": response_data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": {}}, status=status.HTTP_400_BAD_REQUEST)

class GetProfileHomeAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile does not exist for this user"}, status=status.HTTP_404_NOT_FOUND)
        
        # ============================================
        try:
            user_id = request.data.get('user_id')
            target_profile = Profile.objects.get(pk=user_id)
            
            # ============================================
            is_blocked = BlockedUser.objects.filter(i_profile=profile, i_blocked_profile=target_profile).exists()
            if is_blocked:
                return Response({"message": "Blocked user data is not available."}, status=status.HTTP_403_FORBIDDEN)
            
            # ============================================
            dating_preference = DatingPreference.objects.get(i_profile=target_profile)
            dating_preference_serializer = datingserializer(dating_preference)

            # ============================================
            interests = Interest.objects.get(i_profile=target_profile)
            interests_serializer = interestserializer(interests)

            # ============================================
            skin_color = SkinColor.objects.get(i_profile=target_profile)
            skin_color_serializer = skinserializer(skin_color)

            # ============================================
            try:
                auth_user_coordinates = UserCoordinates.objects.get(i_profile=profile)
                auth_coordinates = auth_user_coordinates.current_coordinates
            except UserCoordinates.DoesNotExist:
                auth_coordinates = None
            
            # Get the current coordinates of the target user
            try:
                target_user_coordinates = UserCoordinates.objects.get(i_profile=target_profile)
                target_coordinates = target_user_coordinates.current_coordinates
            except UserCoordinates.DoesNotExist:
                target_coordinates = None
            
            # Calculate the distance between the two sets of coordinates if both exist
            if auth_coordinates and target_coordinates:
                auth_coords = (float(auth_coordinates['current_lat']), float(auth_coordinates['current_long']))
                target_coords = (float(target_coordinates['current_lat']), float(target_coordinates['current_long']))
                distance_in_km = round(distance.distance(auth_coords, target_coords).km, 2)
                distance_in_miles = round(distance_in_km * 0.621371, 2)
            else:
                distance_in_miles = None

            #==========================================================================

            try:
                #target_profile_group_id = PrivateGroupMapp.objects.get(i_profile=target_profile)
                #target_profile_group = target_profile_group_id.i_group
                group_ids = PrivateGroupMapp.objects.filter(i_profile=target_profile).all()
                group_id_list = [str(group.i_group_id) for group in group_ids]
                group_id_str = ",".join(group_id_list)
            except PrivateGroupMapp.DoesNotExist:
                group_id_str = None

            # ============================================
            user_data = {
                'user_id': target_profile.pk,
                'name': target_profile.name,
                'about': target_profile.about,
                'main_image': target_profile.main_image.url if target_profile.main_image else None,
                'gender': target_profile.gender,
                'date_of_birth': target_profile.date_of_birth,
                'height': target_profile.height,
                'weight': target_profile.weight,
                'hair_color': target_profile.hair_color,
                'eye_color': target_profile.eye_color,
                'dating_preference': dating_preference.preference,
                'distance': distance_in_miles,
                'interests': interests.interests,
                'skin_color': skin_color.color,
                'group_id': group_id_str
            }
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User Profile", "data": user_data}, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": 'profile does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
class BlockedProfile(generics.CreateAPIView):
    serializer_class = BlockedProfileSerializer

class UnBlockedProfile(generics.CreateAPIView):
    serializer_class = UnBlockedProfileSerializer

class ListBlockedProfile(APIView):
    def get(self, request, *args, **kwargs):
        resp = {'status': False, 'status_code': status.HTTP_200_OK, 'message': 'No blocked User found', 'data': {}}
        response = []

        query_set = list(BlockedUser.objects.filter(i_profile=request.user.profile, i_blocked_profile__is_delete=False))
        for qs in query_set:
            response.append({
                'block_id': qs.i_blocked_profile.user_id,
                'full_name': qs.i_blocked_profile.name,
                'main_image': qs.i_blocked_profile.main_image.url if qs.i_blocked_profile.main_image else None,
            })

        if response:
            resp['status'] = True
            resp['status_code'] = status.HTTP_200_OK
            resp['message'] = 'Block list view'
            resp['data'] = response
            return Response(resp, status=status.HTTP_200_OK)
        else:
            return Response(resp, status=status.HTTP_200_OK)
        
class GetAboutSingleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        try:
            latest_terms = StaticContent.objects.filter(type="about").latest('id')
            response_data = {
                "introduction": latest_terms.title,
                "description": latest_terms.content
            }
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "About Single", "data": response_data}, status=status.HTTP_200_OK)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Content not Found.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)


        
class GetPrivacyPolicyAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        try:
            latest_terms = StaticContent.objects.filter(type="privacy_policy").latest('id')
            response_data = {
                "privacypolicy": latest_terms.content
            }
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Privacy Policy", "data": response_data}, status=status.HTTP_200_OK)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Content not Found.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)
        


class GetTermsAndConditionsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        try:
            latest_terms = StaticContent.objects.filter(type="terms_and_conditions").latest('id')
            response_data = {
                "text": latest_terms.content
            }
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Terms and Conditions", "data": response_data}, status=status.HTTP_200_OK)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Content not Found.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)

class SendMessageAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        message = request.POST.get('message')
        group_id = request.POST.get('group_id')
        print(message)
        if message is None:
            file = request.FILES.get('file')
            print(file)
            if file is None:
                resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Message field is required', "data": ""}
                return Response(resp)
            # Check if the file type is PDF or image
            allowed_file_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
            if file.content_type not in allowed_file_types:
                resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'File type not appropriate. Only PDF or image files are allowed.', "data": ""}
                return Response(resp)
        if group_id==None:
            resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Group_id field is required', "data": ""}
            return Response(resp)
        
        group_detail = GroupDetail.objects.filter(pk=group_id).first()
        if group_detail==None:
            resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Group does not exist.', "data": ""}
            return Response(resp)
        
        ####### Checking user are blocked by each other ###########
        # sender_blocked = BlockedUser.objects.filter(i_profile=request.user.profile, i_blocked_profile=group_detail.created_by).exists()
        # reciever_blocked = BlockedUser.objects.filter(i_profile=group_detail.created_by, i_blocked_profile=request.user.profile).exists()
        # if sender_blocked:
        #     resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'You blocked this user.', "data": ""}
        #     return Response(resp, status.HTTP_400_BAD_REQUEST)
        # elif reciever_blocked:
        #     resp = {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'You are blocked by this user.', "data": ""}
        #     return Response(resp, status.HTTP_400_BAD_REQUEST)
        
        ##### For Private Message Code ######
        if group_detail.type=='private':
            file = request.FILES.get('file')
            ret = personalmessage(request, group_id, message, file, group_detail.type)
            return Response(ret)
        
        ######## For Group Message Code ##########
        elif group_detail.type=='group':
            file = request.FILES.get('file')
            ret = groupmessage(request, group_id, message, file, group_detail.type)
            return Response(ret)
        
class GetSenderMessagesAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        serializer = GetMessagesSerializer(data=request.data)
        if serializer.is_valid():
            reciepient = serializer.validated_data.get('reciepient')
            sender = request.user.profile.user_id
            messages = Message.objects.filter(sender=sender, reciepient=reciepient)
            serialized_messages = MessageSerializer(messages, many=True)
            #return Response(serialized_messages.data, status=status.HTTP_200_OK)
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "get Send Message", "data": serialized_messages.data}, status=status.HTTP_200_OK)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class RecipientListAPIView(APIView):
    permission_classes = [IsUser]

    def get(self, request, format=None):
        sender = request.user.profile.user_id
        messages = Message.objects.filter(sender=sender)
        recipient_ids = messages.values_list('reciepient', flat=True).distinct()
        recipients_info = []
        for recipient_id in recipient_ids:
            recipient_profile = get_object_or_404(Profile, user_id=recipient_id)
            recipients_info.append({
                'recipient_id': recipient_id,
                'name': recipient_profile.name,
                'main_image': recipient_profile.main_image.url if recipient_profile.main_image else None
            })
        #return Response({'recipients': recipients_info}, status=status.HTTP_200_OK)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Recipient List", "data": recipients_info}, status=status.HTTP_200_OK)

class UserQueryAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        serializer = UserQuerySerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.user.profile.user_id  
            try:
                profile = Profile.objects.get(pk=user_id)
            except Profile.DoesNotExist:
                #return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "User profile not found.", "data": ""}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.validated_data['i_profile'] = profile
            serializer.save()
            
            #return Response({"message": "User query posted successfully."}, status=status.HTTP_201_CREATED)
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User query posted successfully.", "data": ""}, status=status.HTTP_200_OK)
        #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class SignoutAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        serializer = SignoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            #return Response({"message": "User successfully signed out."}, status=status.HTTP_200_OK)
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User successfully signed out.", "data": ''}, status=status.HTTP_200_OK)
        else:
            #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class AdminSignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        admin_role = Role.objects.get(name = 'admin')

        try:
            user = User.objects.create_user(username=username, password=password, is_superuser=True)
            profile = Profile.objects.create(user=user, role=admin_role)
            return Response({"message": "Admin signed up successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminSignInView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = TokenPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
        #if serializer.is_valid():
        #    serializer.save()
        #    return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
        #return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class TermsAndConditionsAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, format=None):
        try:
            terms_conditions = TermsAndConditions.objects.first()
            serializer = termsconditionsserializer(terms_conditions, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except TermsAndConditions.DoesNotExist:
            serializer = termsconditionsserializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class PrivacyPolicyAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, format=None):
        try:
            privacy_policy = PrivacyPolicy.objects.first()
            serializer = privacypolicyserializer(privacy_policy, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except PrivacyPolicy.DoesNotExist:
            serializer = privacypolicyserializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class AboutSingleAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, format=None):
        try:
            about_single = AboutSingles.objects.first()
            serializer = aboutsingleserializer(about_single, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except AboutSingles.DoesNotExist:
            serializer = aboutsingleserializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class StaticContentCreateAPIView(APIView):
    permission_classes = [IsAdmin]
    def post(self, request, *args, **kwargs):
        serializer = StaticContentPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Successfully Created.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class StaticContentGetAPIView(APIView):
    permission_classes = [IsAdmin]
    def get(self, request, *args, **kwargs):
        static = StaticContent.objects.order_by('-id')
        static_serializer = []
        for static_data in static:
            data = {
                "id": static_data.pk,
                "type": static_data.type,
                "title": static_data.title,
                "content": static_data.content
            }
            static_serializer.append(data)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "static content List View.", "data": static_serializer}, status=status.HTTP_200_OK)

class StaticContentDeleteAPI(APIView):
    permission_classes = [IsAdmin]
    def post(self, request):
        try:
            content_id = request.data.get('id')
            if content_id is None:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "ID parameter is required in the request body.", "data": ''}, status=status.HTTP_400_BAD_REQUEST)
            
            content = StaticContent.objects.get(id=content_id)
            content.delete()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Static content deleted successfully.", "data": ''}, status=status.HTTP_200_OK)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Static content with the provided ID does not exist.", "data": ''}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "str(e)", "data": ''}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StaticContentUpdateAPIView(APIView):
    permission_classes = [IsAdmin]
    def post(self, request):
        id = request.data.get('id')
        try:
            static_content = StaticContent.objects.get(id=id)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "StaticContent does not exist.", "data": ''}, status=status.HTTP_404_NOT_FOUND)

        serializer = StaticContentPostSerializer(instance=static_content, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "StaticContent updated successfully.", "data": ''}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ReportsCreateAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, *args, **kwargs):
        reported_by_profile = request.user.profile 
        request.data['reported_by_profile'] = reported_by_profile.pk  
        serializer = ReportsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ReportsListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    queryset = Reports.objects.all()
    serializer_class = ReportsSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        formatted_data = []
        for report in data:
            formatted_report = {
                "report_id": report['id'],
                "username": Profile.objects.get(user_id=report['report_about_message']).name,
                "reported_by": Profile.objects.get(user_id=report['reported_by_profile']).name, 
                "claim": report['claim'],
                "content": report['content'],
                "request": report['request'],
                "response": report['response'],
            }
            formatted_data.append(formatted_report)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": {'reported_data' : formatted_data}}, status=status.HTTP_200_OK)

class ReportsUpdateAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, format=None):
        # Extract data from the request body
        report_id = request.data.get('id')
        request_value = request.data.get('request')
        response_value = request.data.get('response')

        try:
            # Retrieve the Reports instance based on the provided ID
            report_instance = Reports.objects.get(id=report_id)
        except Reports.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Report not found.", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        # Create a serializer instance with the retrieved instance and provided data
        serializer = ReportsUpdateSerializer(instance=report_instance, data={'request': request_value, 'response': response_value}, partial=True)
        
        # Validate and save the serializer
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Report updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Validation error.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ReportsListDeleteAPI(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        try:
            report_id = request.data.get('report_id')
            if report_id is None:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "ID parameter is required in the request body.", "data": ''}, status=status.HTTP_400_BAD_REQUEST)
            
            report = Reports.objects.get(pk=report_id)
            report.delete()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Report deleted successfully.", "data": ''}, status=status.HTTP_200_OK)
        except StaticContent.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Report with the provided ID does not exist.", "data": ''}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "str(e)", "data": ''}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserListView(generics.ListAPIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = Profile.objects.filter(role__name='user').select_related('user')
        user_serializer = []
        for user_profile in users:
            data = {
                'pk': user_profile.user.pk,
                'role': user_profile.role.name,
                'full_name': user_profile.name,
                'email': user_profile.user.email,
                'phone_number': str(user_profile.phone_number),
                'is_active': user_profile.active_status,
                "gender" : user_profile.gender,
                "date_of_birth" :user_profile.date_of_birth,
                "status" : True
            }
            user_serializer.append(data)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User List View.", "data": {'users': user_serializer}}, status=status.HTTP_200_OK)
    
class ProfileActiveStatusUpdateAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = UserActiveDeactiveSerializer(data=request.data)
        if serializer.is_valid():
            pk = serializer.validated_data['pk']
            is_active = serializer.validated_data['is_active']
            try:
                profile = Profile.objects.get(user_id=pk)
                profile.active_status = is_active
                profile.save()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Active status updated successfully.", "data": {}}, status=status.HTTP_200_OK)
            except Profile.DoesNotExist:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Profile with the provided user_id does not exist.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Profile with the provided user_id does not exist.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)
    
class GetQueryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        queries = UserQuery.objects.all().order_by('-id')
        user_data = []
        for user_query in queries:
            #profile_data = {
            #    'user_id': user_query.i_profile.user_id,
            #    'name': user_query.i_profile.name,
            #    'phone_number': str(user_query.i_profile.phone_number),
            #    'email': user_query.i_profile.user.email,
            #}
            query_info = {
                'id': user_query.pk,
                'name': user_query.i_profile.name,
                'phone_number': str(user_query.i_profile.phone_number),
                'email': user_query.i_profile.user.email,
                'subject': user_query.subject,
                'message': user_query.message
            }
            user_data.append(query_info)

        return Response({'data': user_data}, status=status.HTTP_200_OK)

class DeleteQueryAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, format=None):
        query_id = request.data.get('query_id')
        if not query_id:
            return Response({'error': 'Query ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            query = UserQuery.objects.get(pk=query_id)
            query.delete()
            return Response({'message': 'User query deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except UserQuery.DoesNotExist:
            return Response({'error': 'User query not found'}, status=status.HTTP_404_NOT_FOUND)
        
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        return Response({'message': 'Logout Successfull.'}, status= status.HTTP_200_OK)
    
class FcmdeviceAPIView(APIView):
    permission_classes = [IsUser]

    def post(self, request, format=None):
        # Get the user from the request's authentication token
        user = request.user
        user_id = user.id

        # Get the registration_id and type from the request data
        registration_id = request.data.get('registration_id')
        device_type = request.data.get('type')

        # Check if a device with the provided registration_id already exists for the user_id
        existing_device = FCMDevice.objects.filter(user_id=user_id).first()

        if existing_device:
            # Update the existing device's details
            existing_device.registration_id = registration_id
            existing_device.type = device_type
            existing_device.save()
            return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "FCM Device Updated Successfully", "data": {"user_id": user_id, "registration_id": registration_id, "type": device_type}}, status=status.HTTP_200_OK)
        else:
            # Create a new FCM device entry
            FCMDevice.objects.create(user_id=user_id, registration_id=registration_id, type=device_type)
            return Response({"status": True, "status_code": status.HTTP_201_CREATED, "message": "FCM Device Created Successfully", "data": {"user_id": user_id, "registration_id": registration_id, "type": device_type}}, status=status.HTTP_201_CREATED)
    
class AdminNotificationAPIView(APIView):
    serializer_class = AdminNotificationSerializerView
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        distinct_admin_noti_ids = AdminNotificationMapping.objects.values_list('admin_noti_id', flat=True).distinct()
        first_objects = []
        for admin_noti_id in distinct_admin_noti_ids:
            mapping_object = AdminNotificationMapping.objects.filter(admin_noti_id=admin_noti_id).first()
            if mapping_object:
                first_objects.append(mapping_object)
        notification_objects = []

        for mapping_object in first_objects:
            data={"id": mapping_object.notification_id.pk, "notification": mapping_object.notification_id.notification, "title":mapping_object.notification_id.title, "created_on": mapping_object.notification_id.created_on}
            notification_objects.append(data)
        sorted_notification_objects = sorted(notification_objects, key=lambda x: x['id'], reverse=True)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message" : "", "data": sorted_notification_objects})

    def post(self, request, *args, **kwargs):
        message = request.data.get('notification')
        title = request.data.get('title')
        if "notification" not in request.data:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "notification is required field", "data": ""})
        elif "title" not in request.data:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "title is required field", "data": ""})
        start_time = timeit.default_timer()  # Start measuring the overall execution time
        users = Profile.objects.exclude(role__name='admin')
        headers = create_all_usernotification(request, message, title, users)
        execution_time = timeit.default_timer() - start_time  # Calculate the overall execution time
        print(f"Overall execution time: {execution_time} seconds")
        print("===================================================")
        serialized_users = serialize('python', users)
        response_data = {"status": True, "status_code": status.HTTP_201_CREATED, "message": "Notification send to all users", "data": serialized_users}
        return Response(response_data)

class CreateAdminNotification(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = AdminNotificationCreate

class FAQuery(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = FAQSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class FAQueryGet(APIView):
    permission_classes = [IsUser]

    def get(self, request, *args, **kwargs):
        try:
            faqs = StaticContent.objects.filter(type="faq").values('id', 'title', 'content')
            
            if faqs.exists():
                response_data = []
                
                for faq in faqs:
                    response_data.append({
                        "id": faq['id'],
                        "question": faq['title'],
                        "answer": faq['content'],
                    })
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "FAQ", "data": response_data}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "No FAQ found.", "data": {}}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status": False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "error", "data": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ChatHomeInheritance(ChatHomeAll, APIView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response_data = response.data
        group_list_copy = list()
        friend_list = []
        if response_data['status']:
            block_profile_list = list(BlockedUser.objects.filter(
                    i_profile=request.user.profile, i_blocked_profile__is_delete=False
                    ).values_list('i_blocked_profile',flat = True).distinct())
            blocked_by_profile = list(BlockedUser.objects.filter(
                    i_blocked_profile=request.user.profile, i_profile__is_delete=False
                    ).values_list('i_profile',flat = True).distinct())
            block_profile_list += blocked_by_profile
            for group_data in response_data['data']['group_list']:
                group_obj = GroupDetail.objects.get(id=group_data['id'])
                
                group_data['disabled'] = False
                if group_obj.created_by.user.profile.pk not in block_profile_list:
                    group_data['disabled'] = True
                #group_data['verify'] = group_obj.created_by.is_verify
                social_user = SocialAccount.objects.filter(user__pk= group_obj.created_by.user.pk)
                if social_user.exists():
                    social_uid = social_user[0].uid
                    friend_list.append(social_uid)
                else:
                    friend_list.append(str(group_obj.created_by.user.pk))
                group_list_copy.append(group_data)

            response_data['data']['group_list'] = group_list_copy
            response_data['data']['status_id'] = list(friend_list)
        return Response(response_data)
    
class ConversationSearch(ChatHomeAll, APIView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response_data = response.data
        group_list_copy = list()
        friend_list = []

        search_keyword = request.query_params.get('search_keyword', '').strip()

        if not search_keyword:
            # No search keyword provided, follow the original API behavior
            if response_data['status']:
                block_profile_list = list(BlockedUser.objects.filter(
                        i_profile=request.user.profile, i_blocked_profile__is_delete=False
                        ).values_list('i_blocked_profile', flat=True).distinct())
                blocked_by_profile = list(BlockedUser.objects.filter(
                        i_blocked_profile=request.user.profile, i_profile__is_delete=False
                        ).values_list('i_profile', flat=True).distinct())
                block_profile_list += blocked_by_profile

                for group_data in response_data['data']['group_list']:
                    group_obj = GroupDetail.objects.get(id=group_data['id'])

                    group_data['disabled'] = group_obj.created_by.user.profile.pk not in block_profile_list
                    social_user = SocialAccount.objects.filter(user__pk=group_obj.created_by.user.pk)

                    if social_user.exists():
                        social_uid = social_user[0].uid
                        friend_list.append(social_uid)
                    else:
                        friend_list.append(str(group_obj.created_by.user.pk))
                    
                    group_list_copy.append(group_data)

                response_data['data']['group_list'] = group_list_copy
                response_data['data']['status_id'] = list(friend_list)

        else:
            response = super().get(request, *args, **kwargs)
            response_data = response.data
            group_list_copy = []
            friend_list = []

            if response_data['status']:
                block_profile_list = list(BlockedUser.objects.filter(
                    i_profile=request.user.profile, i_blocked_profile__is_delete=False
                ).values_list('i_blocked_profile', flat=True).distinct())
                blocked_by_profile = list(BlockedUser.objects.filter(
                    i_blocked_profile=request.user.profile, i_profile__is_delete=False
                ).values_list('i_profile', flat=True).distinct())
                block_profile_list += blocked_by_profile

                for group_data in response_data['data']['group_list']:
                    group_obj = GroupDetail.objects.get(id=group_data['id'])
                    group_data['disabled'] = group_obj.created_by.user.profile.pk not in block_profile_list

                # Filter group by group_name if search_keyword is provided
                    if search_keyword:
                        group_name = group_obj.get_group_name()  # Use custom method to get group name
                        if search_keyword.lower() in group_name.lower():
                            social_user = SocialAccount.objects.filter(user__pk=group_obj.created_by.user.pk)
                            if social_user.exists():
                                social_uid = social_user[0].uid
                                friend_list.append(social_uid)
                            else:
                                friend_list.append(str(group_obj.created_by.user.pk))
                            group_list_copy.append(group_data)
                    else:
                    # If no search_keyword provided, add group data to group_list_copy as-is
                        social_user = SocialAccount.objects.filter(user__pk=group_obj.created_by.user.pk)
                        if social_user.exists():
                            social_uid = social_user[0].uid
                            friend_list.append(social_uid)
                        else:
                            friend_list.append(str(group_obj.created_by.user.pk))
                        group_list_copy.append(group_data)

                response_data['data']['group_list'] = group_list_copy
                response_data['data']['status_id'] = list(friend_list)

        return Response(response_data)
class GetMessageInheritance(GetMessage, APIView):
     def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response_data = response.data
        if response_data['status']:
            group_obj = GroupDetail.objects.get(pk=int(request.GET.get('i_group')))
            #response_data['data']['verify'] = group_obj.created_by.is_verify
            response_data['data']['image'] = group_obj.created_by.get_main_image()
            response_data['data']['is_blocked'] = True if BlockedUser.objects.filter(
                Q(i_profile = request.user.profile,i_blocked_profile = group_obj.created_by.user.profile)|
                Q(i_blocked_profile = request.user.profile,i_profile = group_obj.created_by.user.profile)
                ).exists() else False
            social_user = SocialAccount.objects.filter(user__pk= group_obj.created_by.user.pk)
            if social_user.exists():
                social_uid = social_user[0].uid
                response_data['data']['status_id'] = social_uid
            else:
                response_data['data']['status_id'] = str(group_obj.created_by.user.pk)
            response_data['data']['group_id'] = int(request.GET.get('i_group'))
            response_data['data']['profile_id'] = group_obj.created_by.user.profile.pk
        return Response(response_data)
     
class DeleteAccount(generics.DestroyAPIView):
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        user = self.request.user

        # Delete associated data from other models
        user.profile.delete()  # Delete Profile model associated with the user
        BlockedUser.objects.filter(i_profile=user.profile).delete()  # Delete BlockedUser entries associated with the user's profile
        DatingPreference.objects.filter(i_profile=user.profile).delete()  # Delete DatingPreference entries associated with the user's profile
        Interest.objects.filter(i_profile=user.profile).delete()  # Delete Interest entries associated with the user's profile
        SkinColor.objects.filter(i_profile=user.profile).delete()  # Delete SkinColor entries associated with the user's profile
        UserCoordinates.objects.filter(i_profile=user.profile).delete()  # Delete UserCoordinates entries associated with the user's profile
        UserQuery.objects.filter(i_profile=user.profile).delete()  # Delete UserQuery entries associated with the user's profile

        # Delete GroupDetail entries associated with the user's created groups
        GroupDetail.objects.filter(created_by=user.profile).delete()

        # Delete associated mappings
        PrivateGroupMapp.objects.filter(i_profile=user.profile).delete()
        PublicGroupMapp.objects.filter(i_profile=user.profile).delete()

        # Delete FirestoreGroupMapp entries associated with the user's groups
        FirestoreGroupMapp.objects.filter(i_group__created_by=user.profile).delete()

        # Finally, delete the user
        user.delete()

        #return Response({"message": "Account and associated data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"status": True, "status_code": status.HTTP_204_NO_CONTENT, "message": "Account and associated data deleted successfully.", "data": ''}, status=status.HTTP_204_NO_CONTENT)
    
class UpdateNotificationViewInhertiance(UpdateNotificationView, APIView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        data_list = list()
        if response.data['status']:
            exclude_notification = NotificationType.objects.filter(
                type_name__in=['message', "call_initiate", "call_rejected", 
                               "call_recieved", "call_cancelled_by_user"]
                               ).values_list('type_name', flat=True)
            for notification_data in response.data['data']:
                if notification_data['type'] not in exclude_notification:
                    data_list.append(notification_data)
            response.data['data'] = data_list
        return Response(response.data,status=response.data.get('status_code',200))