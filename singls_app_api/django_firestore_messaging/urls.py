from django.urls import path, include
from .views import *

urlpatterns = [
    path('gen_id_jwt/', getuidtoken.as_view(), name="generate_firebase_token"),
    path('create_firestore_group/', CreateFirestoreId.as_view(), name="create_firestore"),
]
