from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django_chat import urls
from django_firestore_messaging import urls
from django_rest_authentication.authentication import urls
from django_notification import urls
from user_management.chat_urls import urlpatterns as chaturlpattern

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user_management/', include('user_management.urls')),
    path('auth/', include('django_rest_authentication.authentication.urls')),
    path('notify/', include('django_notification.urls')),
    path('subscription/', include('subscription.urls')),
    path('chat/', include(chaturlpattern)),
]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
