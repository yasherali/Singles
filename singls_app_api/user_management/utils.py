from datetime import datetime
from django.urls import reverse
import magic
import phonenumbers
import re
import base64

from .models import *
from django.apps import apps
from django.core.files.base import ContentFile
from .models import Profile
from django.db.models import Q
from rest_framework import status
from django.db.models import Sum
from django_firestore_messaging.models import *
from django_notification.models import *
from django_notification.utils import *
from django_chat.models import *
from django_chat.utils import *
from firebase_admin import firestore
from django.shortcuts import get_object_or_404


def create_firebase_profile_signup(profile):
    try:
        # Check if the profile already exists in PrivateGroupMapp
        existing_private_mapping = PrivateGroupMapp.objects.filter(i_profile=profile)
        if existing_private_mapping.exists():
            group_id = existing_private_mapping.first().i_group_id
            # Check if the group_id exists in FirestoreGroupMapp
            existing_firestore_mapping = FirestoreGroupMapp.objects.filter(i_group_id=group_id)
            if existing_firestore_mapping.exists():
                # If the mappings exist, return success response without creating new details
                return {'status': True, 'message': 'Profile already exists.'}
        
        # If mappings do not exist, generate new details
        collection_name = 'groups'
        group_name = 'inbox_' + profile.user.first_name
        db = firestore.client()
        document_data = {
            'group_name': group_name,
            'group_type': 'private'
        }

        # Create the document in the collection
        collection_ref = db.collection(collection_name)
        document_ref = collection_ref.add(document_data)
        document_id = document_ref[1].id

        # Create a subcollection within the document
        subcollection_name = 'chat'
        subcollection_ref = document_ref[1].collection(subcollection_name)
        subcollection_ref.document().set({})

        # Save details in the database
        group = GroupDetail(group_name=group_name, created_by=profile)
        group.save()

        firestore_mapping = FirestoreGroupMapp.objects.create(i_group=group, firestore_id=document_id)
        firestore_mapping.save()

        private_group_mapping = PrivateGroupMapp.objects.create(i_profile=profile, i_group=group)
        private_group_mapping.save()

        # Return success response
        #return {'status': True, 'message': 'Group Chat Document and subcollection created successfully'}
    
    except Exception as e:
        resp = {'status': False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), "data": ""}
        return resp
    
    return {'status': True, "status_code": status.HTTP_201_CREATED, 'message': "Firebase firestore id is created", "data": ""}


def get_firestore_id(profile):
    try:
        # Check if there is a mapping in PrivateGroupMapp
        private_mapping = PrivateGroupMapp.objects.filter(i_profile=profile)
        if private_mapping.exists():
            group_id = private_mapping.first().i_group_id
            # Check if there is a corresponding firestore_id in FirestoreGroupMapp
            firestore_mapping = FirestoreGroupMapp.objects.filter(i_group_id=group_id)
            if firestore_mapping.exists():
                return firestore_mapping.first().firestore_id
        return None
    except Exception as e:
        return None

def get_profiles(many = False, query = None, **kwargs):
    profile_qs = None
    if many == True:
       profile_qs = Profile.objects.filter(**kwargs)
        
    if many == False:
        profile_qs = Profile.objects.filter(**kwargs).first()
    
    if query is not None and many == True:
        profile_qs=Profile.objects.filter(query)
       
    return profile_qs

    
def get_roles(role):
    if role:
        user_role = Role.objects.filter(id = role).first()
        return user_role
    else:
        return Role.objects.all()
    
def get_user_roles():
    return list(Role.objects.values_list('name','display_name'))


def get_model_objects(app_label, model_name, list_ids):
    if list_ids == []:
        return None
    else:
        data = apps.get_model(app_label=app_label, model_name=model_name).objects.filter(id__in=list_ids)
    return data if data else None


def decode_base64_file(base64_file):
    # Remove the base64 prefix
    if base64_file.startswith('data:'):
        data = base64_file.split(';base64,', 1)[1]
    else:
        data = base64_file

    try:
        # Decode the Base64 data
        decoded_file = base64.b64decode(data)
    except UnicodeDecodeError:
        return None

    # Validate the file format based on the signature
    mime_type = magic.from_buffer(decoded_file, mime=True)
    file_extension = mime_type.split('/')[-1]
    if file_extension not in ['jpeg', 'jpg', 'png', 'pdf']:
        return None

    # Create a ContentFile from the decoded file
    file = ContentFile(decoded_file, name='file.' + file_extension)
    return file



def validate_phone_number(value, country_short_form):
    phone_number = re.sub(r'\D', '', value)
    try:
        parsed_number = phonenumbers.parse(phone_number, country_short_form)
        if not phonenumbers.is_valid_number(parsed_number):
            return {'success':False, 'message':'Invalid phone number.'}
        else:
            return {'success':True, 'message':'Correct number.'}
    except phonenumbers.NumberParseException:
        return {'success':False, 'message':'Invalid phone number format or country Code.'}

########### This Function is to create single user notification entry
def singleusernotification(message, push_notifi_message, title, reciever_id, type, type_name, content='', sender_id=None):
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
    

def checknotificationtype(name):
    noti_type = NotificationType.objects.filter(type_name=name).first()
    return noti_type

def personalmessage(request, group_id, message, file, type):
    sender_profile = request.user.profile
    recie = PrivateGroupMapp.objects.get(i_group=group_id)
    ########### Checking Friend Status ###############
    # friend_exist = Friend.objects.filter(i_profile=request.user.profile, i_fprofile=recie.i_profile).exists()
    # if friend_exist==False:
    #     return {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'You need to be friend for send message.', "data": ""}
    noti_type = checknotificationtype('message')
    if recie.i_profile.is_delete==True:
        return {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'No user found.', "data": ""}
    firestore_obj = FirestoreGroupMapp.objects.get(i_group=recie.i_group, i_group__type="private")
    fire_id = firestore_obj.firestore_id

    #firestore_obj = get_object_or_404(FirestoreGroupMapp, i_group=recie.i_group, i_group__type="private")
    #fire_id = firestore_obj.firestore_id
    
    timestamp = datetime.now().isoformat()
    message_save = Message.objects.create(message=message, sender=request.user.profile, chat_media=file, reciepient = recie.i_profile, type=type, i_group=recie.i_group)
    if message_save.chat_media:
        media = message_save.chat_media.url
    else:
        media = ''

    db = firestore.client()
    document_data = {
        'message_id' : message_save.pk,
        'sender': sender_profile.pk,
        "sender_name": sender_profile.get_full_name(),
        # "sender_name": request.user.first_name+' '+request.user.last_name,
        'recipient': recie.i_profile.pk,
        'message': message,
        'chat_media': media,
        'timestamp': timestamp,
        'type': type,
        'i_group' : fire_id
    }

    collection_ref = db.collection('groups').document(fire_id).collection("chat")
    document_ref = collection_ref.document()
    document_ref.set(document_data)
    
    # read = read_by.objects.create(message_id=message_save, i_profile=recipient)
    
    read = ReadBy.objects.create(message_id=message_save, i_profile=recie.i_profile)
    ##### Sending push notification on create of message ######
    if not MuteMessage.objects.filter(i_profile=recie.i_profile, m_profile = request.user.profile).exists():
        try:
            type = noti_type.id
            type_name = noti_type.type_name
            title = noti_type.title
            message = f"New message from {sender_profile.get_full_name()}"
            push_notifi_message = f"New message from {sender_profile.get_full_name()}"
            group_detail = GroupDetail.objects.get(created_by=request.user.profile, type="private")
            content = {
                "sender_name": request.user.profile.get_full_name(),
                "i_group": group_detail.pk,
                "sender_id": request.user.profile.pk
                }
            
            ret = singleusernotification(message, push_notifi_message, title, recie.i_profile.pk, type, type_name, content, request.user.profile.pk)
            print(message, "--------")
            
            return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}
        except Exception as e:
            return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
    return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}

def groupmessage(request, group_id, message, file, type):
    sender = request.user.profile.pk
    firestore_obj = GroupDetail.objects.get(id=group_id)
    fire_id_1 = FirestoreGroupMapp.objects.get(i_group=firestore_obj.id)
    fire_id= fire_id_1.firestore_id
    # print(fire_id)
    timestamp = datetime.now().isoformat()

    message_save = Message.objects.create(message=message, sender=request.user.profile, chat_media=file, type=type, i_group=firestore_obj)
    
    if message_save.chat_media:
        media = message_save.chat_media.url
    else:
        media = ''
    db = firestore.client()
    document_data = {
        'message_id' : message_save.pk,
        'sender': sender,
        # "sender_name": request.user.first_name+' '+request.user.last_name,
        "sender_name": request.user.first_name,
        # 'recipient': str(recipient),
        'message': message,
        'chat_media': media,
        'timestamp': timestamp,
        'type': type,
        'i_group' : fire_id
    }
    noti_type = checknotificationtype('message')
    try:
        collection_ref = db.collection('groups').document(fire_id).collection("chat")
        document_ref = collection_ref.document()
        document_ref.set(document_data)
        group_mem_list = Profile.objects.filter(publicgroupmapp__i_group=group_id).exclude(pk=request.user.profile.pk).values_list('pk', flat=True).distinct()
        
        group_details = PrivateGroupMapp.objects.filter(i_profile__in=group_mem_list).values_list('i_group', flat=True).distinct()
        
        firestore_group = FirestoreGroupMapp.objects.filter(i_group__in=group_details).values_list('firestore_id', flat=True).distinct()
        ######## Group Members send Notification ###################
        for i in group_mem_list:
            rec_profile = Profile.objects.get(pk=i)
            ReadBy.objects.create(message_id = message_save, i_profile=rec_profile)
            type = noti_type.id
            type_name = noti_type.type_name
            title = "Message recieved"
            message = "New message from {sender_name}"
            push_notifi_message = f"New message from {request.user.profile.get_full_name()}"
            group_detail = GroupDetail.objects.get(created_by=request.user.profile, type="private")
            content = {
                "sender_name": request.user.profile.get_full_name(),
                "i_group": group_detail.pk,
                "sender_id": request.user.profile.pk
                }

            ret = singleusernotification(message, push_notifi_message, title, rec_profile.pk, type, type_name, content, sender)
            
        for i in firestore_group:
            collection_ref = db.collection('groups').document(i).collection("chat")
            document_ref = collection_ref.document()
            document_ref.set(document_data)
        return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}
    except Exception as e:
        return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
    
