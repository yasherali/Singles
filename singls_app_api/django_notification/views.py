from django.shortcuts import render
from .models import *
from django.http import HttpResponse
from firebase_admin.messaging import Message
from .serializers import *
from rest_framework import generics ,permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import create_all_usernotification, notification_count_api
from user_management.models import Profile
import timeit

################ Notification View and Create Api #################
class NotificationView(generics.ListCreateAPIView):
    # queryset = Notification.objects.get()
    serializer_class = AdminNotificationSerializerView

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

    def create(self, request, *args, **kwargs):
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
        response_data = {"status": True, "status_code": status.HTTP_201_CREATED, "message": "Notification send to all users", "data": ""}
        return Response(response_data)

class CreateAdminNotification(generics.CreateAPIView):
    serializer_class = AdminNotificationCreate

############### Get User Notifications #####################
class UpdateNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the resource object
        try:
            resources = Notification.objects.filter(reciever_profile=request.user.profile).order_by('-pk')
            serializer = NotificationSerializerView(resources, many=True)
            response_data = {"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": serializer.data}
            Notification.objects.filter(reciever_profile=request.user.profile, is_read=False).update(is_read=True)
            return Response(response_data)
        except Notification.DoesNotExist:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "", "data": ""})

     
    def patch(self, request, pk):
        obj = Notification.objects.get(pk=pk)

        serializer = NotificationSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status' : True,
                'message' : serializer.data
            })
        else:
            return Response({
                'status' : False,
                'message' : serializer.errors
            })
        
############### Notification Mute Unmute #############
class NotificationSetting(APIView):
    def get(self, request):
        user_id = request.user.profile.pk
        profile =Profile.objects.get(pk=user_id)
        if profile.notification==True:
            profile.notification=False
        else:
            profile.notification=True
        profile.save()
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Notification setting updated", "data":""})
    
############ Notification List Alert API #################
class NotificationList(APIView):
    def get(self, request):
        user_profile = request.user.profile
        ret = notification_count_api(user_profile)
        return Response(ret)
    

def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "AIzaSyDU7FfvaQzK3QgWcl6x03QNKMqq0ayOC1E",' \
         '        authDomain: "cmdjango.firebaseapp.com",' \
         '        databaseURL: "https://cmdjango-default-rtdb.firebaseio.com",' \
         '        projectId: "cmdjango",' \
         '        storageBucket: "cmdjango.appspot.com",' \
         '        messagingSenderId: "312645201583",' \
         '        appId: "1:312645201583:web:59f43fd6b97410aad96e5a",' \
         '        measurementId: "G-6K30F0M6MG"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data,content_type="text/javascript")

################# Views Code ########################

class CategoryNotification(APIView):
    def post(self, request):
        message = request.data.get('notification')
        title = request.data.get('title')
        category = request.data.get('category')
        if "notification" not in request.data:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "notification is required field", "data": ""})
        elif "title" not in request.data:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "title is required field", "data": ""})
        elif "category" not in request.data:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "category is required field", "data": ""})
        # categories = UserCategory.objects.filter(pk=category).first()
        # if categories is None:
        #     return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Category not found", "data": ""})
        start_time = timeit.default_timer()  # Start measuring the overall execution time
        # headers = create_category_usernotification(request, message, title, categories)
        execution_time = timeit.default_timer() - start_time  # Calculate the overall execution time
        print(f"Overall execution time: {execution_time} seconds")
        print("===================================================")
        response_data = {"status": True, "status_code": status.HTTP_201_CREATED, "message": "Notification send to all users", "data": ""}
        return Response(response_data)
        