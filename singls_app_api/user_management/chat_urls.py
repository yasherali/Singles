from .views import ChatHomeInheritance,GetMessageInheritance, ConversationSearch
from django_chat.views import read_message as ReadMessage
from django_chat.views import SendMessage, ChatSearchFriend
from django.urls import path, include

urlpatterns = [
    path('send_message/', SendMessage.as_view(), name="send_message"),
    path('chat_home_all/', ChatHomeInheritance.as_view(), name="chat_home_all"),
    path('get_message/', GetMessageInheritance.as_view(), name="get_message"),
    path('message_read/', ReadMessage.as_view(), name='message_read'),
    path('chat_search/', ChatSearchFriend.as_view()),
    path('conversation_search/', ConversationSearch.as_view())
]