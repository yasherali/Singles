from django.urls import path, include
from .views import *

urlpatterns = [
    path('create_group/', CreateGroupApi.as_view(), name="create_group"),
    path('send_message/', SendMessage.as_view(), name="new_msg_send"),
    path('add_member/', AddGroupMember.as_view(), name="add_member"),
    # path('user_list/', OpenChatApi.as_view(), name="chat_home"),
    path('group_user_list/', GroupUserList.as_view(), name="user_list"),
    path('get_messages/', GetMessage.as_view(), name="message_list"),
    path('update_chat_activity/', UserLastActivity.as_view(), name="update_chat_activity"),
    path('message_read/', read_message.as_view(), name="read_message"),
    path('chat_home/', homescreen_user_list.as_view(), name="user_list"),
    path('chatsearch/', ChatSearchFriend.as_view(), name="chatsearch"),
    path('mutefriend/', MuteFriend.as_view(), name="mute_friend"),
    path('unmutefriend/', UnMuteFriend.as_view(), name="unmute_friend"),
    path('chat_home_all/', ChatHomeAll.as_view(), name="chat_home_all"),
]
