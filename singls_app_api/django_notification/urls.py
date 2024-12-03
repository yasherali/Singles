from .views import *
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from django.urls import path, include

# router = DefaultRouter()
# router.register(r'abcs', NotificationView, basename='abc')
# urlpatterns = router.urls

urlpatterns = [
    path('notify_view/', NotificationView.as_view()), ## this route is for view notification and create notification
    path('update/<int:pk>/', UpdateNotificationView.as_view()), #This route is use for update in a notification
    path('firebase-messaging-sw.js/',showFirebaseJS,name="show_firebase_js"),
    path('devices/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'), #This url is for register new device in FCMDevice  model
    path('usernotification/', UpdateNotificationView.as_view()), #This route is use for update in a notification
    path('notification_setting/', NotificationSetting.as_view()),
    path('notificationlist/', NotificationList.as_view(), name="notificationlist"),
    path('category_notification/',CategoryNotification.as_view(), name='category_notification'),
    path('createadminnotification/', CreateAdminNotification.as_view(), name='create')
]
