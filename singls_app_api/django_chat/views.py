from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import firestore
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .utils import personal_message, group_message, private_message_view, group_message_view, home_chat_screen, home_chat_screen_with_group, check_notification_type
from rest_framework import status
from django_notification.utils import single_user_notification
from django_notification.models import Notification

################################################# WORKING ON NEW MODEL ###############################################    

############### Create Public Group Api ####################
class CreateGroupApi(APIView):
    def post(self, request):
        collection_name = 'groups'
        # group_name = request.POST.get('group_name')
        group_name = request.POST.get('group_name')
        if group_name is None or group_name=="":
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "group_name is required field", "data": ""})
        db = firestore.client()
        document_data = {
            'group_name': group_name,
            'group_type' : "public"
        }

        # Create the document in the collection
        try:
            collection_ref = db.collection(collection_name)
            document_ref = collection_ref.add(document_data)
            document_id = document_ref[1].id
            # Create a subcollection within the document
            
            subcollection_name = 'chat'
            subcollection_ref = document_ref[1].collection(subcollection_name)
            subcollection_ref.document().set({})
            
            model_data = {
                'i_firestore' : document_id,
                'name' : group_name,
                'i_profile' : request.user.id,
                'group_type' : "public"
            }
            group = GroupDetail(group_name=group_name, created_by=request.user.profile, type="group")
            group.save()
            
            data = FirestoreGroupMapp.objects.create(i_group=group, firestore_id=document_id)
            data.save()
            pub_group = PublicGroupMapp.objects.create(i_profile=request.user.profile, i_group=group)
            pub_group.save()
            return Response({'status': True, "status_code": status.HTTP_201_CREATED, 'message': 'Chat group is created successfully', "data": ""})
        except Exception as e:
            return Response({'status': False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), "data":""})

############### Add Group Member API ################
class AddGroupMember(APIView):
    def post(self, request):
        profile_id = request.POST.get('i_profile')
        group_id = request.POST.get('i_group')
        user_exists = PublicGroupMapp.objects.filter(i_group=group_id, i_profile=profile_id)
        if not user_exists.exists():
            serializer = AddGroupMemberSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                group_detail = GroupDetail.objects.get(pk=request.POST.get('i_group'))
                ######## Notification ###################
                type = "other"
                title = "Added in Group"
                message = "You are added in group {group_name}"
                push_notifi_message = f"You are added in group {group_detail.group_name}"
                content = {
                    "group_name": group_detail.group_name,
                    "i_group": group_detail.pk
                    }
                noti = check_notification_type('add_chat_grp_member')
                ret = single_user_notification(message, push_notifi_message, title, request.POST.get('i_profile'), noti.id, noti.type_name, content, request.user.profile.pk)
                resp = {'status': True, "status_code": status.HTTP_201_CREATED, "message": "New member is added", 'data': serializer.data}
                return Response(resp)
            else:
                resp = {'status': False, "status_code": status.HTTP_400_BAD_REQUEST, "message": serializer.errors, 'data' : ""}
                return Response(resp)
        else:
            resp = {'status': False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "You are already member of group", 'data' : ""}
            return Response(resp, status=status.HTTP_400_BAD_REQUEST)
        

############### SEND MESSAGE API #################
class SendMessage(APIView):
    permission_classes = [IsAuthenticated]
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
            ret = personal_message(request, group_id, message, file, group_detail.type)
            return Response(ret)
        
        ######## For Group Message Code ##########
        elif group_detail.type=='group':
            file = request.FILES.get('file')
            ret = group_message(request, group_id, message, file, group_detail.type)
            return Response(ret)
            
################# OPENNING CHAT MAIN SCREEN ##################
# class OpenChatApi(APIView):
#     permission_classes = []
#     def get(self, request):
#         user_id = request.user.profile.pk
#         try:
#             firestore_id = FirestoreGroupMapp.objects.get(i_group__created_by = request.user.profile, i_group__type="private").firestore_id
#         except:
#             return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND ,"message": "Firebase id is not found", "data": ""})
#         # ret = home_connection_list(request, user_id, firestore_id)
#         return Response("Function is commented kindly uncommit it")
    
############### GET MESSAGE LIST OF SPECIFIC GROUP ##################
class GetMessage(APIView):
    def get(self, request):
        sender_id = request.user.profile.pk
        
        reciever_id = request.query_params.get('i_group')
        
        if reciever_id==None:
            return Response({'status':False, 'status_code': status.HTTP_400_BAD_REQUEST, 'message':'i_group is required field', 'data': ""})
        try:
            group = GroupDetail.objects.get(pk=reciever_id)
        except GroupDetail.DoesNotExist:
            resp={'status':False, 'status_code': status.HTTP_404_NOT_FOUND, 'message':'Group does not exist', 'data': ""}
            return Response(resp)
        if group.type=="private":
            ret = private_message_view(request, reciever_id, sender_id)
            return Response(ret)
        else:
            ret = group_message_view(request, reciever_id, sender_id, group)
            return Response(ret)

################ Last Activity of user Not Used At a time #########################
class UserLastActivity(APIView):
    def post(self, request):
        if request.POST.get('connect_id'):
            profile_obj = self.request.user.profile
            activity = UserActivity.objects.get(i_profile=profile_obj.pk)
            activity.last_activity = timezone.now()
            activity.conn_profile = request.POST.get('connect_id')
            activity.save()
            return Response({"status": True, "status_code":status.HTTP_200_OK, "message": "updated last activity", "data":""})
        else:
            ret = {"status": False, "status_code":status.HTTP_400_BAD_REQUEST, "message": "connect_id field is required", "data":""}
            return Response(ret)
        

############### Read Message Api ###########################
class read_message(APIView):
    def post(self, request):
        message_id = request.POST.get("message_id")
        if message_id==None or message_id=="":
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "Message_id is required field", "data": ""})
        try:
            message = ReadBy.objects.get(message_id=message_id)
            message_obj = Message.objects.filter(pk=message_id).first()
            noti = Notification.objects.filter(sender_profile=message_obj.sender, reciever_profile=message_obj.reciepient, type__type_name='message', is_read=False).update(is_read=True)
        except:
            return Response({"status": False, "status_code": status.HTTP_404_NOT_FOUND, "message": "Message_id is not found", "data": ""})
        message.read = True
        message.save()
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Message read status updated", "data": ""})
    
############### Home Screen Of Chat #########################
class homescreen_user_list(APIView):
    def get(self, request):
        current_user_profile = request.user.profile
        ret = home_chat_screen(request, current_user_profile)
        return Response(ret)

############## Group User List ######################
class GroupUserList(APIView):
    def post(self, request):
        group_id = request.POST.get('i_group')
        group_mem_list = Profile.objects.filter(publicgroupmapp__i_group=group_id)#.values_list('id', 'first_name').distinct()
        serializer = UserListSerializer(group_mem_list, many=True)
        resp = {'status' : True, 'status_code': status.HTTP_200_OK, 'message': "", 'data': serializer.data}
        return Response(resp)
    

############## Group User List ######################
class ChatSearchFriend(APIView):
    def post(self, request):
        keyword = request.POST.get('search')
        if keyword==None:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "search is required field", "data": ""})
        print(keyword)
        # resp = search_friends_by_name(request, keyword)
        return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "", "data": "function is commented uncomment it"})
    
########## Mute User Friends ######################
class MuteFriend(APIView):
    def post(self, request):
        i_profile = request.POST.get("profile_id")
        profile = Profile.objects.filter(pk=i_profile).first()
        if profile!=None:
            if not MuteMessage.objects.filter(i_profile=request.user.profile, m_profile = profile).exists():
                MuteMessage.objects.create(i_profile = request.user.profile, m_profile = profile)
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User is muted", "data": ""})
            else:
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "Already muted", "data": ""})
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "User not found", "data": ""})

########## UnMute User Friends ######################        
class UnMuteFriend(APIView):
    def post(self, request):
        i_profile = request.POST.get("profile_id")
        profile = Profile.objects.filter(pk=i_profile).first()
        if profile!=None:
            if MuteMessage.objects.filter(i_profile=request.user.profile, m_profile = profile).exists():
                message = MuteMessage.objects.get(i_profile = request.user.profile, m_profile = profile)
                message.delete()
                return Response({"status": True, "status_code": status.HTTP_200_OK, "message": "User is unmute", "data": ""})
            else:
                return Response({"status": False, "status_code": status.HTTP_200_OK, "message": "Not found mute data", "data": ""})
        else:
            return Response({"status": False, "status_code": status.HTTP_400_BAD_REQUEST, "message": "User not found", "data": ""})
        
########## Chat Home All Users ######################
class ChatHomeAll(APIView):
    def get(self, request):
        current_user_profile = request.user.profile
        ret = home_chat_screen_with_group(request, current_user_profile)
        return Response(ret)
    

