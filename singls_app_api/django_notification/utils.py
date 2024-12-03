from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message as Msg
from firebase_admin.messaging import Notification as Notifi
from user_management.models import Profile
from rest_framework.response import Response
from rest_framework import status
from .serializers import NotificationSerializer
# from social_app.models import Friend
from firebase_admin import firestore
from django_firestore_messaging.models import *
from django_chat.models import *
from django.db.models import Count
from .models import *
# from social_app.models import GroupMember, Group
import timeit
# from user_management.utils import get_user_category, get_user_age

########### This Function is to send notification to all user devices
def sendnotificationall(message, title, regis_id=None):
    try:
        if regis_id is None:
            devices = FCMDevice.objects.all()
        else:
            devices = regis_id
        dev = devices.send_message(Msg(notification=Notifi(title=title, body=message)))
        return "success"
    except:
        return "no device found"

def sendnotification(message, reciever_id, title):
    try:
        profile = Profile.objects.filter(user=reciever_id).first()
        devices = FCMDevice.objects.filter(user_id=profile.user.pk, active = True).last()
        print(devices.registration_id)
        if devices:
            devices.send_message(Msg(notification=Notifi(title=title, body=message)))
            # print(devices)
            return "success"
        print("no device found")
    except:
        return "no device found"
    






# def sendnotification_data_key(reciever_id, data):
#     try:
#         import requests,json
#         profile = Profile.objects.filter(user=reciever_id).first()
#         devices = FCMDevice.objects.filter(user_id=profile.user.pk)
#         print(devices,'Fcm devices found')
#         if devices:
#             for device in devices:
#                 url = "https://fcm.googleapis.com/fcm/send"
#                 payload = {'to': device.registration_id, 'data': data, 'content_available': True}
#                 headers = {
#                     'Content-Type': 'application/json',
#                     'Authorization': 'key=AAAACKkmntw:APA91bEjRf7OntNhPCzPHdx2AkxT24XmnnPcdg3L-gSF2cG8cfmEh-2ddcbd7jarrY5mdM2PLEW-fwlw1ttlHZ5cP5ms1F2Qpy_ES6QMZEIN9-lWZ8qLMPTrFTvUWvfzzjx2XiuYqqBC'
#                 }
#                 payload_json = json.dumps(payload)

#                 print(url,'url')
#                 print()
#                 print(payload,'payload')
#                 print()
#                 print(headers,'headers')
                
#                 response = requests.post(url, headers=headers, json=payload)
#                 print(response,"================5555================")
                
#                 if response.status_code == 200:
#                     print("Notification sent successfully")
#                 else:
#                     print(f"Failed to send notification, status code: {response.status_code}")

#             # Your existing logic for Msg and devices.send_message
#             return "success"
#         else:
#             print("No device found")
#             return "No device found"
#     except Exception as e:
#         print(f"Error sending notification: {repr(e)}")
#         return "Error sending notification"



def sendnotification_data_key(reciever_id, data):
    try:
        profile = Profile.objects.filter(user=reciever_id).first()
        print(profile.get_full_name())
        devices = FCMDevice.objects.filter(user_id=profile.user.pk, active = True).last()
        print(devices.registration_id)

        if devices:
            mgs = Msg(
                    data=data,
                )
            print(type(mgs))
            devices.send_message(mgs)
            return "success"
        print("no device found")
    except Exception as e:
        print(str(e))
        return "no device found"

def sendnotification_data_key_call(reciever_id, data):
    try:
        profile = Profile.objects.filter(user=reciever_id).first()
        devices = FCMDevice.objects.filter(user_id=profile.user.pk, active = True).last()
        print(devices)
        if devices:
            mgs = Msg(
                    data=data,
                )
            devices.send_message(mgs)
            return "success"
        print("no device found")
    except:
        return "no device found"















# def sendnotification_data_key(reciever_id, data):
#     try:
#         profile = Profile.objects.filter(user=reciever_id).first()
#         devices = FCMDevice.objects.filter(user_id=profile.user.pk)
#         if devices:
         
#             if devices.type == 'ios':
#                 # for ios devices

#                 # mgs = Msg(
#                 #         data=data,
#                 #         # content_available = True
#                 #     )
#                 kwargs = {
#                         "content_available": True,
#                         'extra_kwargs': {"priority": "high", "mutable_content": True, 'notification':data },
#                 }
#                 check = devices.send_message(sound='default', **kwargs)
#                 print('check ', check)
#                 return "success"
#             else:
#                 # for android devices
#                 mgs = Msg(
#                         data=data,
#                     )
#                 # devices.send_message(mgs)
#                 dev = devices.send_message(mgs)
#                 print(dev)
#                 return "success"
#         print("no device found")
#     except Exception as e:
#         print(repr(e))
#         return "no device found"
## Sample data variables ###    
# {
#                     "title" : title,
#                     "body" : message,
#                     "type" : "video call"
#             }

########### This Function is to create all user notification entry
def create_all_usernotification(request, message, title, users):
    db = firestore.client()

    ##### Create AdminNotification Model Entry
    admin_noti = AdminNotification(sender_id=request.user.profile)
    admin_noti.save()
    
    ##### Create Firestore Database Notification Batch Entries
    total_users = users.count()
    processed_users = 0
    batch_size = 500
    
    
    print(total_users)
    loop_start_time = timeit.default_timer()  # Start measuring the While loop execution time
    while processed_users < total_users:
        
        batch_users = users[processed_users:processed_users+batch_size]
        # Process the batch of users
        # print(len(batch_users))
        # print(batch_users)
        batch_ref = db.batch()
        for_loop_start_time = timeit.default_timer()  # Start measuring the for loop execution time
        for user in batch_users:          
            try:
                noti_obj = Notification.objects.create(notification=message, title=title,is_read=False, reciever_profile=user, sender_profile=None)
                AdminNotificationMapping.objects.create(admin_noti_id = admin_noti, notification_id=noti_obj, is_sent=True)
                serializer = NotificationSerializer(noti_obj)
                fire_id = FirestoreGroupMapp.objects.filter(i_group__created_by=user.pk, i_group__type='private').values_list('firestore_id', flat=True).first()
                notifications_collection_ref = db.collection('groups').document(fire_id).collection("notification")
                new_notification_doc_ref = notifications_collection_ref.document()

                # Add the set operation to the batch
                batch_ref.set(new_notification_doc_ref, serializer.data)
            except Exception as e:
                print(e)
            
        for_loop_execution_time = timeit.default_timer() - for_loop_start_time  # Calculate the for loop execution time
        print(f"For loop execution time: {for_loop_execution_time} seconds")
        batch_start_time = timeit.default_timer()
        batch_ref.commit()
        batch_commit_execution_time = timeit.default_timer() - batch_start_time  # Calculate the for loop execution time
        print(f"batch_commit_execution_time: {batch_commit_execution_time} seconds")
        processed_users += batch_size
    loop_execution_time = timeit.default_timer() - loop_start_time  # Calculate the loop execution time
    print(f"While Loop execution time: {loop_execution_time} seconds")

    success = sendnotificationall(message, title)
    
    return "send notification succesfully"

########### This Function is to create single user notification entry
def single_user_notification(message, push_notifi_message, title, reciever_id, type, type_name, content='', sender_id=None):
    notification_check = Profile.objects.get(pk=reciever_id)
    if notification_check.notification==False:
        return {'status': True, 'status_code': status.HTTP_200_OK, 'message': "Notification is OFF", 'data': ''}
    # if sender_id is None:
    #     sender = Profile.objects.filter(role='admin').first()
    #     sender_id = sender.pk
    # users = Profile.objects.get(pk=reciever_id)
    db = firestore.client()
    
    fire_id = FirestoreGroupMapp.objects.filter(i_group__created_by=reciever_id, i_group__type='private').values_list('firestore_id', flat=True).first()
    
    notification_data = {
            "title": title,
            "notification": message,
            "is_read": False,
            "reciever_profile": reciever_id,
            "sender_profile": sender_id,
            "type": type,
            "content": content,
        }
    

    serializer = NotificationSerializer(data=notification_data)
    if serializer.is_valid():
        serializer.save()
        data = serializer.data
        data["content"] = content
        data["type"] = type_name
        try:
            collection_ref = db.collection('groups').document(fire_id).collection("notification")
            document_ref = collection_ref.document()
            document_ref.set(data)
        except Exception as e:
            return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
        response_data = {"status": True, 'status_code': status.HTTP_200_OK, "message": "", "data": data}
        sendnotification(push_notifi_message, reciever_id, title)
        # firebase_count_increase(reciever_id)
        return response_data
    else:
        response_data = {"status": False, 'status_code': status.HTTP_400_BAD_REQUEST, "message": serializer.errors, "data": ""}
        return response_data
    

############## This function is used to send data key notification ################
def data_key_notification(message, title, reciever_id, type, type_name, content='', sender_id=None):
    notification_check = Profile.objects.get(pk=reciever_id)
    # if notification_check.notification==False:
    #     print("notification_check.notification")
    #     return {'status': True, 'status_code': status.HTTP_200_OK, 'message': "Notification is OFF", 'data': ''}
    db = firestore.client()

    print(db,"database")
    
    fire_id = FirestoreGroupMapp.objects.filter(i_group__created_by=reciever_id, i_group__type='private').values_list('firestore_id', flat=True).first()
    
    notification_data = {
            "title": title,
            "notification": message,
            "is_read": False,
            "reciever_profile": reciever_id,
            "sender_profile": sender_id,
            "type": type,
            "content": content,
        }
    

    serializer = NotificationSerializer(data=notification_data)
    if serializer.is_valid():
        serializer.save()
        data = serializer.data
        data["content"] = content
        data["type"] = type_name
        try:
            print('try')
            collection_ref = db.collection('groups').document(fire_id).collection("notification")
            document_ref = collection_ref.document()
            document_ref.set(data)
        except Exception as e:
            print(repr(e),"iii")
            return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
        response_data = {"status": True, 'status_code': status.HTTP_200_OK, "message": "", "data": data}
        ret = sendnotification_data_key(reciever_id, content)
        print(ret,"sendnotification_data_key")
        # firebase_count_increase(reciever_id)
        return response_data
    else:
        response_data = {"status": False, 'status_code': status.HTTP_400_BAD_REQUEST, "message": serializer.errors, "data": ""}
        print(serializer.errors,"serializer is not valid")
        return response_data

########### Firebase Notification Count Increase #########
def firebase_count_increase(profile_id):
    try:
        firestore_id = FirestoreGroupMapp.objects.filter(i_group__profile_group__i_profile=profile_id).values_list('firestore_id', flat=True).first()
        # print(firestore_id)
    except FirestoreGroupMapp.DoesNotExist:
        return {"status": False,'status_code': status.HTTP_404_NOT_FOUND, "message": "firestore_id not found", "data": ""}
    # Access Firestore database
    db = firestore.client()

    try:
        # Fetch user document
        user_doc_ref = db.collection('groups').document(firestore_id)
        user_doc = user_doc_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            notification_count = user_data.get('notification_count')
            if notification_count is None:
                # Create notification_count field with default value of 1
                user_doc_ref.update({'notification_count': 1})
                notification_count = 1
            else:
                notification_count+=1
                user_doc_ref.update({'notification_count': notification_count})
            return {'notification_count': notification_count}
        else:
            # Create user document with notification_count field set to 1
            user_doc_ref.set({'notification_count': 1})
            return {'notification_count': 1}
    except Exception as e:
        return {'error': str(e)}
    
############## Firebase Count Remove #############
def firebase_count_remove(profile_id):
    try:
        firestore_id = FirestoreGroupMapp.objects.filter(i_group__profile_group__i_profile=profile_id).values_list('firestore_id', flat=True).first()
        print(firestore_id)
    except FirestoreGroupMapp.DoesNotExist:
        return {"status": False, 'status_code': status.HTTP_404_NOT_FOUND, "message": "firestore_id not found", "data": ""}
    # Access Firestore database
    db = firestore.client()

    try:
        print(firestore_id)
        # Fetch user document
        user_doc_ref = db.collection('groups').document(firestore_id)
        user_doc = user_doc_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            notification_count = user_data.get('notification_count')
            if notification_count is None:
                # Create notification_count field with default value of 1
                print("before update")
                user_doc_ref.update({'notification_count': 0})
                notification_count = 0
                print(notification_count)
            else:
                print("else")
                notification_count = 0
                user_doc_ref.update({'notification_count': notification_count})
                print("after update")
            return {'notification_count': notification_count}
        else:
            # Create user document with notification_count field set to 1
            user_doc_ref.set({'notification_count': 0})
            return {'notification_count': 1}
    except Exception as e:
        return {'error': str(e)}
    
############### Notification Count Api #########################
def notification_count_api(user_profile):
    notification_data = {}
    # Retrieve the ReadBy objects for the authenticated user where read=False
    # Check if there are any unread notifications for the user
    has_unread_notifications = Notification.objects.filter(reciever_profile=user_profile, is_read=False).exists()

    if has_unread_notifications:
        notification_data["notification"] = True
    else:
        notification_data["notification"] = False

    unread_readby_objects = ReadBy.objects.filter(i_profile=user_profile, read=False)
    total_unread_count = Message.objects.filter(message_seen__in=unread_readby_objects).count()
    notification_data["total_message_count"] = total_unread_count
    # Get the corresponding messages and group them by sender
    unread_messages_count = (
        Message.objects
        .filter(message_seen__in=unread_readby_objects)
        .values('sender')
        .annotate(unread_count=Count('sender'))
    )
    data = []
    # Access the sender and unread count in each group
    for entry in unread_messages_count:
        sender_id = entry['sender']
        unread_count = entry['unread_count']
        
        # Perform any desired operations with the sender and unread count
        user_list = {sender_id: unread_count}
        data.append(user_list)
    notification_data["message_count"] = data
    return {"status": True, "status_code": status.HTTP_200_OK, "message": "" ,"data":notification_data}
    
################### Get request of notification data #########################
def update_notification(message, push_notifi_message, title, reciever_id, type, sender_id, content=''):
    db = firestore.client()
    
    fire_id = FirestoreGroupMapp.objects.filter(i_group__created_by=reciever_id, i_group__type='private').values_list('firestore_id', flat=True).first()
    noti = Notification.objects.filter(sender_profile=sender_id, reciever_profile=reciever_id, type="message").last()
    notification_data = {
            "title": title,
            "notification": message,
            "is_read": False,
            "reciever_profile": reciever_id,
            "sender_profile": sender_id,
            "type": type,
            "content": content,
        }
    if noti.is_read==False:
        noti.delete()
    serializer = NotificationSerializer(noti, data=notification_data)

    if serializer.is_valid():
        serializer.save()
        serializer.data["content"] = content
        try:
            collection_ref = db.collection('groups').document(fire_id).collection("notification")
            document_ref = collection_ref.document()
            document_ref.set(serializer.data)
        except Exception as e:
            return {'status': False, 'status_code': status.HTTP_403_FORBIDDEN, 'message': str(e), 'data': ''}
        response_data = {"status": True, 'status_code': status.HTTP_200_OK, "message": "", "data": serializer.data}
        sendnotification(push_notifi_message, reciever_id, title)
        # firebase_count_increase(reciever_id)
        return response_data
    

############## This function is used to update read satatus ##############
def UpdateNotificationStatus(rec_profile, noti_type):
    noti = Notification.objects.filter(reciever_profile=rec_profile, type=noti_type, is_read=False).update(is_read=True)
    return noti


############## This function is used to send data key notification ################
def data_key_notification_call(message, title, reciever_id, type, type_name, content='', sender_id=None):
    notification_check = Profile.objects.get(pk=reciever_id)
    # if notification_check.notification==False:
    #     print("notification_check.notification")
    #     return {'status': True, 'status_code': status.HTTP_200_OK, 'message': "Notification is OFF", 'data': ''}
    db = firestore.client()

    print(db,"database")
    
    fire_id = FirestoreGroupMapp.objects.filter(i_group__created_by=reciever_id, i_group__type='private').values_list('firestore_id', flat=True).first()
    
    notification_data = {
            "title": title,
            "notification": message,
            "is_read": False,
            "reciever_profile": reciever_id,
            "sender_profile": sender_id,
            "type": type,
            "content": content,
        }
    

    serializer = NotificationSerializer(data=notification_data)
    if serializer.is_valid():
        serializer.save()
        data = serializer.data
        data["content"] = content
        data["type"] = type_name
        try:
            print('try')
            collection_ref = db.collection('groups').document(fire_id).collection("notification")
            document_ref = collection_ref.document()
            document_ref.set(data)
        except Exception as e:
            print(repr(e),"iii")
            return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
        response_data = {"status": True, 'status_code': status.HTTP_200_OK, "message": "", "data": data}
        ret = sendnotification_data_key_call(reciever_id, content)
        print(ret,"sendnotification_data_key")
        # firebase_count_increase(reciever_id)
        return response_data
    else:
        response_data = {"status": False, 'status_code': status.HTTP_400_BAD_REQUEST, "message": serializer.errors, "data": ""}
        print(serializer.errors,"serializer is not valid")
        return response_data