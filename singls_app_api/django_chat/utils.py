from firebase_admin import firestore
from rest_framework.response import Response
from datetime import datetime
from .models import *
from .serializers import *
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from django_notification.utils import single_user_notification, update_notification
from rest_framework import status
from django.db.models import Q, Subquery, OuterRef, Max
from django_notification.models import Notification, NotificationType

################## Check Notification Types #################
def check_notification_type(name):
    noti_type = NotificationType.objects.filter(type_name=name).first()
    return noti_type

################## Send One to One Messages ##################
def personal_message(request, group_id, message, file, type, reel_id = None, video_type = None, reel_media = False):
    sender = request.user.profile.pk
    recie = PrivateGroupMapp.objects.get(i_group=group_id)
    ########### Checking Friend Status ###############
    # friend_exist = Friend.objects.filter(i_profile=request.user.profile, i_fprofile=recie.i_profile).exists()
    # if friend_exist==False:
    #     return {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'You need to be friend for send message.', "data": ""}
    noti_type = check_notification_type('message')
    if recie.i_profile.is_delete==True:
        return {'status': False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'No user found.', "data": ""}
    firestore_obj = FirestoreGroupMapp.objects.get(i_group=recie.i_group, i_group__type="private")
    fire_id = firestore_obj.firestore_id
    
    timestamp = datetime.now().isoformat()

    if reel_id is not None and video_type is not None and reel_media == True:
        message_save = Message(
            message=message,
            sender=request.user.profile, 
            chat_media=file, 
            reciepient=recie.i_profile, 
            type=type, 
            i_group=recie.i_group,
            reel_id = reel_id,
            video_type = video_type, 
            media = reel_media
        )
    else:
        message_save = Message(
            message=message,
            sender=request.user.profile, 
            chat_media=file, 
            reciepient=recie.i_profile, 
            type=type, 
            i_group=recie.i_group
        )

    # IT WILL ONLY WORKS WHEN USER HAVE A LANGUAGE, OTHERWISE SET TO ENGLISH
    try:
        message_save.language = request.user.profile.language.code
    except:
        pass 

    message_save.save()

    if message_save.chat_media:
        media = message_save.chat_media.url
    else:
        media = ''

    db = firestore.client()

    if reel_id is not None and video_type is not None and reel_media == True:
        media = file
        document_data = {
            'message_id' : message_save.pk,
            'sender': sender,
            "sender_name": request.user.first_name,
            # "sender_name": request.user.first_name+' '+request.user.last_name,
            'recipient': recie.i_profile.pk,
            'message': message,
            'chat_media': media,
            'timestamp': timestamp,
            'type': type,
            'i_group' : fire_id,
            'receiver_language': message_save.language,
            'reel_id' : reel_id,
            'video_type' : video_type,
            "media" : reel_media
        }
    else:
        document_data = {
            'message_id' : message_save.pk,
            'sender': sender,
            "sender_name": request.user.first_name,
            # "sender_name": request.user.first_name+' '+request.user.last_name,
            'recipient': recie.i_profile.pk,
            'message': message,
            'chat_media': media,
            'timestamp': timestamp,
            'type': type,
            'i_group' : fire_id,
            'receiver_language': message_save.language
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
            message = noti_type.message
            push_notifi_message = f"New message from {request.user.profile.get_full_name()}"
            group_detail = GroupDetail.objects.get(created_by=request.user.profile, type="private")
            content = {
                "sender_name": request.user.profile.get_full_name(),
                "i_group": group_detail.pk,
                "sender_id": request.user.profile.pk
                }
            
            ret = single_user_notification(message, push_notifi_message, title, recie.i_profile.pk, type, type_name, content, request.user.profile.pk)
            
            return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}
        except Exception as e:
            return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
    return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}
    

############### Send Group Chat Messages #################
def group_message(request, group_id, message, file, type):
    sender = request.user.profile.pk
    firestore_obj = GroupDetail.objects.get(id=group_id)
    fire_id_1 = FirestoreGroupMapp.objects.get(i_group=firestore_obj.id)
    fire_id= fire_id_1.firestore_id
    # print(fire_id)
    timestamp = datetime.now().isoformat()

    message_save = Message(
        message=message, 
        sender=request.user.profile, 
        chat_media=file, 
        type=type, 
        i_group=firestore_obj
    )
    # IT WILL ONLY WORKS WHEN USER HAVE A LANGUAGE, OTHERWISE SET TO ENGLISH
    try:
        message_save.language = request.user.profile.language.code
    except:
        pass 

    message_save.save()

    
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
        'i_group' : fire_id,
        'receiver_language': message_save.language
    }
    noti_type = check_notification_type('message')
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

            ret = single_user_notification(message, push_notifi_message, title, rec_profile.pk, type, type_name, content, sender)
            
        for i in firestore_group:
            collection_ref = db.collection('groups').document(i).collection("chat")
            document_ref = collection_ref.document()
            document_ref.set(document_data)
        return {'status': True, 'status_code': status.HTTP_201_CREATED, 'message': 'Message created successfully', 'data': ""}
    except Exception as e:
        return {'status': False, 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), 'data': ''}
    
################ Get One to One Messages #################
def private_message_view(request, reciever_id, sender_id):
    try:
        group1 = PrivateGroupMapp.objects.get(i_group=reciever_id)
    except PrivateGroupMapp.DoesNotExist:
        resp={'status':False, 'status_code': status.HTTP_404_NOT_FOUND, 'message':"Group doesn't exist", 'data': ""}
        return Response(resp)
    i_gr_rec = group1.i_profile.pk
    list_reciever = list(Message.objects.filter(reciepient=request.user.pk, sender=i_gr_rec).values_list('pk', flat=True))
    # print(list_reciever)
    ready_by = ReadBy.objects.filter(message_id__in= list_reciever).update(read=True)

    firestore_id = FirestoreGroupMapp.objects.get(i_group__created_by = request.user.profile, i_group__type="private").firestore_id

    group_message = Message.objects.filter(Q(sender=sender_id) | Q(reciepient=sender_id)).filter(Q(sender=group1.i_profile) | Q(reciepient=group1.i_profile))

    user = User.objects.get(id=group1.i_profile.pk)
    serializer = MessageSerializer(group_message, many=True)
    for data in serializer.data:
        if data['sender'] == sender_id:
            data['direction'] = "sender"
        else:
            data['direction'] = "receiver"
    data1 = serializer.data
    sorted_data = sorted(data1, key=lambda data1: data1["id"])
    is_mute = MuteMessage.objects.filter(i_profile=request.user.profile, m_profile = group1.i_profile).exists()
    name = group1.i_profile.get_full_name()
    noti = Notification.objects.filter(reciever_profile=request.user.profile, sender_profile = group1.i_profile, type__type_name='message', is_read=False).update(is_read=True)
    return {'status': True, 'status_code':status.HTTP_200_OK, 'message': "", "data":{'id': user.pk, 'name': name, 'firestore_id': firestore_id, 'is_mute': is_mute, 'message': sorted_data}}


################ Get Group Message View ######################
def group_message_view(request, reciever_id, sender_id, group):
    messages = Message.objects.filter(i_group_id=reciever_id)

    list_reciever = list(Message.objects.filter(i_group=reciever_id).values_list('pk', flat=True))
    ready_by = ReadBy.objects.filter(message_id__in= list_reciever, i_profile=sender_id).update(read=True)

    firestore_id = FirestoreGroupMapp.objects.get(i_group = reciever_id).firestore_id
    
    serializer = GroupMessageSerializer(messages, many=True)
    for data in serializer.data:
        # print("data: ",data)
        if data['sender'] == sender_id:
            data['direction'] = "sender"
        else:
            name = Profile.objects.get(pk=data['sender']).get_full_name()
            data['sender_name'] = name
            data['direction'] = "receiver"
    return {'status': True, 'status_code':status.HTTP_200_OK, 'message': "", "data":{"group_id": reciever_id, "name": group.group_name,'firestore_id': firestore_id, 'message': serializer.data}}


############# Chat Home Screen with Group Chat  ################
def home_chat_screen_with_group(request, current_user_profile):
    try:
        firestore_id = FirestoreGroupMapp.objects.get(i_group__created_by = current_user_profile, i_group__type="private").firestore_id
    except:
        return {"status": False, "status_code": status.HTTP_400_BAD_REQUEST ,"message": "Firebase id is not found", "data": ""}

    # friend_profiles = Friend.objects.filter(i_profile=current_user_profile).values_list('i_fprofile', flat=True)

    ######### Extract user profiles of friends
    merged_profiles = list(Profile.objects.filter(Q(message_sender__reciepient=current_user_profile) | Q(message_reciever__sender=current_user_profile)).values_list('pk').distinct())
    ######### Retrieve private group details of friends
    private_groups = GroupDetail.objects.filter(type='private', profile_group__i_profile__in=merged_profiles)

    ######### Adding Publib Group Detail in which user Add ############
    public_mappings = PublicGroupMapp.objects.filter(i_profile=request.user.profile)

    # Extract the GroupDetail objects from the mappings
    group_details_pub = GroupDetail.objects.filter(id__in=public_mappings.values_list('i_group', flat=True))
    # Perform union on the querysets
    group_details = private_groups.union(group_details_pub)

    serializer = GroupDetailSerializer(group_details, many=True)

    data = serializer.data
    ########### Get Users Last Message and their time ################
    distinct_users = Profile.objects.filter(Q(message_sender__reciepient=current_user_profile) | Q(message_reciever__sender=current_user_profile)).distinct()

    distinct_users3 = distinct_users.annotate(
        last_message=Subquery(
            Message.objects.filter(
                Q(sender=OuterRef('pk'), reciepient=current_user_profile) | Q(sender=current_user_profile, reciepient=OuterRef('pk'))
            ).order_by('-created_at').values('message')[:1]
        ),
        last_message_language=Subquery(
            Message.objects.filter(
                Q(sender=OuterRef('pk'), reciepient=current_user_profile) | Q(sender=current_user_profile, reciepient=OuterRef('pk'))
            ).order_by('-created_at').values('language')[:1]
        ),
        last_message_time=Subquery(
            Message.objects.filter(
                Q(sender=OuterRef('pk'), reciepient=current_user_profile) | Q(sender=current_user_profile, reciepient=OuterRef('pk'))
            ).order_by('-created_at').values('created_at')[:1]
        )
    )

    # Query to get the count of unread messages of type 'group' for each i_group
    unread_messages_counts = Message.objects.filter(
        type='group',  # Filter by message type 'group'
        i_group__isnull=False,  # Filter for messages associated with a group
        message_seen__read=False,  # Filter for unread messages
        message_seen__i_profile=request.user.profile  # Filter for the specific profile
    ).values('i_group').annotate(unread_count=Count('pk')).order_by('i_group')
    # Query to get the count of Group Chat Messages ######
    last_messages = Message.objects.filter(
        i_group__isnull=False,  # Filter for messages associated with a group
        type='group',  # Filter by message type 'group'
    ).values('i_group').annotate(
        last_message_time=Max('created_at'),
        last_message=Max('message')
    ).order_by('i_group')
    # Fetch the message IDs from ReadBy model where type is 'private'
    private_message_ids = ReadBy.objects.filter(i_profile=request.user.profile.pk, read=False, message_id__type='private').values_list('message_id', flat=True)

    # Get the count of message IDs grouped by i_group in Message model for 'private' type messages
    private_message_count_by_group = Message.objects.filter(id__in=private_message_ids, type='private').values('i_group', 'sender').annotate(count=Count('id'))

    # print(f"data => {data}")
    ####### Appending last message and last message time in all group Data ###########
    for group1 in data:
        if group1["type"]=="private":
            group_one = GroupDetail.objects.get(pk=group1["id"])
            # profile_data = Profile.objects.get(pk=group1["created_by"])
            for profile in distinct_users3:            
                if group1["created_by"]==profile.pk:
                    group1["user_id"] = profile.pk
                    group1["last_message"] = profile.last_message
                    group1["last_message_language"] = profile.last_message_language
                    group1["message_time"] = profile.last_message_time
            group1["user_id"] = group1["created_by"]
            group1["group_name"] = group_one.get_group_name()
            group1["group_image"] = group_one.get_group_image()
            for i in private_message_count_by_group:
                group_id = GroupDetail.objects.filter(created_by=i['sender'], type="private").values_list('pk', flat=True).first()
                if group1["id"]==group_id:
                    group1["unread"] = i["count"]
            if 'unread' not in group1:
                group1["unread"] = 0
            if 'last_message' not in group1:
                group1["last_message"] = None
                group1["last_message_language"] = None
                group1["message_time"] = None

        elif group1["type"]=='group':
            group_one = GroupDetail.objects.get(pk=group1["id"])
            group1["group_name"] = group_one.get_group_name()
            group1["group_image"] = group_one.get_group_image()
            for i in unread_messages_counts:
                if group1["id"]==i["i_group"]:
                    group1["unread"] = i["unread_count"]
            for j in last_messages:
                if group1["id"]==j["i_group"]:
                    group1["last_message"] = j['last_message']
                    group1["last_message_language"] = profile.last_message_language
                    group1["message_time"] = j['last_message_time']
            if 'unread' not in group1:
                group1["unread"] = 0
            if 'last_message' not in group1:
                group1["last_message"] = None
                group1["message_time"] = None

    sorted_data = sorted(data, key=lambda x: "message_time" not in x)
    new_data = sorted_data[data.count({"message_time": None}) :] + sorted_data[: data.count({"message_time": None})]
    
    sorted_data = sorted(new_data, key=lambda x: (x["message_time"] is not None, x["message_time"] or ""), reverse=True)
    
    # Remove dictionaries with last_message = null

    group_list = [group for group in sorted_data if group["last_message"] is not None]
    #### Above line commented for vifty reel share ########
    # group_list = sorted_data

    return {"status": True, "status_code": status.HTTP_200_OK, "message": "" ,"data":{"firestore_id": firestore_id, "group_list": group_list}}#, "status_id": list(friend_profiles)}}


############### Current Using Home Chat Screen ############
def home_chat_screen(request, current_user_profile):
    try:
        firestore_id = FirestoreGroupMapp.objects.get(i_group__created_by = current_user_profile, i_group__type="private").firestore_id
    except:
        return {"status": False, "status_code": status.HTTP_400_BAD_REQUEST ,"message": "Firebase id is not found", "data": ""}

    # friend_profiles = Friend.objects.filter(i_profile=current_user_profile).values_list('i_fprofile', flat=True)

    ######### Extract user profiles of friends
    merged_profiles = list(Profile.objects.filter(Q(message_sender__reciepient=current_user_profile) | Q(message_reciever__sender=current_user_profile)).values_list('pk').distinct())
    
    ######### Retrieve private group details of friends
    private_groups = GroupDetail.objects.filter(type='private', profile_group__i_profile__in=merged_profiles)

    serializer = GroupDetailSerializer(private_groups, many=True)

    data = serializer.data
    ########### Get Users Last Message and their time ################
    distinct_users = Profile.objects.filter(Q(message_sender__reciepient=current_user_profile) | Q(message_reciever__sender=current_user_profile)).distinct()

    distinct_users3 = distinct_users.annotate(
        last_message=Subquery(
            Message.objects.filter(
                Q(sender=OuterRef('pk'), reciepient=current_user_profile) | Q(sender=current_user_profile, reciepient=OuterRef('pk'))
            ).order_by('-created_at').values('message')[:1]
        ),
        last_message_time=Subquery(
            Message.objects.filter(
                Q(sender=OuterRef('pk'), reciepient=current_user_profile) | Q(sender=current_user_profile, reciepient=OuterRef('pk'))
            ).order_by('-created_at').values('created_at')[:1]
        )
    )
    # Fetch the message IDs from ReadBy model where type is 'private'
    private_message_ids = ReadBy.objects.filter(i_profile=request.user.profile.pk, read=False, message_id__type='private').values_list('message_id', flat=True)

    # Get the count of message IDs grouped by i_group in Message model for 'private' type messages
    private_message_count_by_group = Message.objects.filter(id__in=private_message_ids, type='private').values('i_group', 'sender').annotate(count=Count('id'))

    ####### Appending last message and last message time in all group Data ###########
    for group1 in data:
        if group1["type"]=="private":
            profile_data = Profile.objects.get(pk=group1["created_by"])
            for profile in distinct_users3:            
                if group1["created_by"]==profile.pk:
                    group1["user_id"] = profile.pk
                    group1["group_image"] = profile.get_main_image()
                    group1["last_message"] = profile.last_message
                    group1["message_time"] = profile.last_message_time
            group1["user_id"] = group1["created_by"]
            group1["group_name"] = profile_data.get_full_name()
            group1["group_image"] = profile_data.get_main_image()

        for i in private_message_count_by_group:
            group_id = GroupDetail.objects.filter(created_by=i['sender'], type="private").values_list('pk', flat=True).first()
            if group1["id"]==group_id:
                group1["unread"] = i["count"]
        if 'unread' not in group1:
            group1["unread"] = 0
        if 'last_message' not in group1:
            group1["last_message"] = None
            group1["message_time"] = None

    sorted_data = sorted(data, key=lambda x: "message_time" not in x)
    new_data = sorted_data[data.count({"message_time": None}) :] + sorted_data[: data.count({"message_time": None})]
    
    sorted_data = sorted(new_data, key=lambda x: (x["message_time"] is not None, x["message_time"] or ""), reverse=True)
    
    # Remove dictionaries with last_message = null
    group_list = [group for group in sorted_data if group["last_message"] is not None]

    return {"status": True, "status_code": status.HTTP_200_OK, "message": "" ,"data":{"firestore_id": firestore_id, "group_list": group_list}}#, "status_id": list(friend_profiles)}}


# def check_pre_msg_notifi(user1, user2):
#     noti = Notification.objects.filter(sender_profile=user1, reciever_profile=user2, type="message").last()
#     if noti is None:
#         return False
#     else:
#         if noti.is_read==False:
#             return True
#     return False

############ Chat Search Friend Api Function ##########
# def search_friends_by_name(request, name):
#     friend_list = []
#     friends = list(Friend.objects.filter(i_profile=request.user.profile, i_fprofile__user__first_name__icontains=name))
#     # print(friends)
#     for i in friends:
#         data = {
#             "group_id" : GroupDetail.objects.filter(created_by=i.i_fprofile, type="private").values_list("pk", flat=True).first(),
#             "fullname" : i.i_fprofile.get_full_name(),
#             "group_image" : i.i_fprofile.get_main_image(),
#             "user_id" : i.i_fprofile.pk
#         }
#         friend_list.append(data)
#     return friend_list
