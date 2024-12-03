from firebase_admin import firestore
from .models import *
from rest_framework import status
from firebase_admin import auth

############### This API is to create firebase profile by Hitting API ###############
def create_firebase_profile(profile):
    collection_name = 'groups'
    group_name = 'inbox_'+profile.user.first_name
    db = firestore.client()
    document_data = {
        'group_name': group_name,
        'group_type' : 'private',
        'notification_count' : 0
    }

    # Create the document in the collection
    try:
        collection_ref = db.collection(collection_name)
        document_ref = collection_ref.add(document_data)
        document_id = document_ref[1].id
        print(document_id)
        # Create a subcollection within the document
        
        subcollection_name = 'chat'
        subcollection_ref = document_ref[1].collection(subcollection_name)
        subcollection_ref.document().set({})
        # print(profile.pk)
        model_data = {
            'i_firestore' : document_id,
            'name' : group_name,
            'i_profile' : profile.pk
        }
        group = GroupDetail(group_name=group_name, created_by=profile)
        group.save()
        
        data = FirestoreGroupMapp.objects.create(i_group=group, firestore_id=document_id)

        data.save()
        pri_group = PrivateGroupMapp.objects.create(i_profile=profile, i_group=group)
        pri_group.save()
        # return Response({'status': True, 'message': 'Group Chat Document and subcollection created successfully'})
    except Exception as e:
        resp = {'status': False, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e), "data": ""}
        return resp
    return {'status': True, "status_code": status.HTTP_201_CREATED, 'message': "Firebase firestore id is created", "data": ""}

################# This Function is for Create User Friebase Profile in SignUp API #####################
def create_firebase_profile_signup(profile):
    collection_name = 'groups'
    group_name = 'inbox_'+profile.user.first_name
    db = firestore.client()
    document_data = {
        'group_name': group_name,
        'group_type' : 'private'
    }

    # Create the document in the collection
    try:
        collection_ref = db.collection(collection_name)
        document_ref = collection_ref.add(document_data)
        document_id = document_ref[1].id
        print(document_id)
        # Create a subcollection within the document
        
        subcollection_name = 'chat'
        subcollection_ref = document_ref[1].collection(subcollection_name)
        subcollection_ref.document().set({})
        # print(profile.pk)
        model_data = {
            'i_firestore' : document_id,
            'name' : group_name,
            'i_profile' : profile.pk
        }
        group = GroupDetail(group_name=group_name, created_by=profile)
        group.save()
        
        data = FirestoreGroupMapp.objects.create(i_group=group, firestore_id=document_id)

        data.save()
        pri_group = PrivateGroupMapp.objects.create(i_profile=profile, i_group=group)
        pri_group.save()
        # return Response({'status': True, 'message': 'Group Chat Document and subcollection created successfully'})
    except Exception as e:
        resp = {'status': False, 'message': str(e)}
        return resp
    resp = signin_firebase(profile)
    return resp

################ Sign-In Function ##############
def signin_firebase(profile):
    uid = str(profile.pk)
    # Create a custom token
    custom_token = auth.create_custom_token(uid)
    # Print the generated custom token
    # print(custom_token)
    return custom_token.decode('ASCII')

def get_firestore_id(profile):
    try:
        i_group = GroupDetail.objects.get(created_by=profile.pk, type="private")
        firestore_id = FirestoreGroupMapp.objects.get(i_group=i_group.pk)
        firestore_id = firestore_id.firestore_id
        return firestore_id
    except:
        return None