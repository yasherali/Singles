from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework import generics
# Create your views here.

######### Generate JWT Token For Firebase Authentication ######################
class getuidtoken(generics.CreateAPIView):
    serializer_class = CreateFirebaseUid
    

############ Creating Firebase Firestore Groupt Entry Of User ####################
class CreateFirestoreId(generics.CreateAPIView):
    serializer_class = CreateFirebaseGroup