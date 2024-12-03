from rest_framework import permissions
from .models import Notification
from rest_framework.permissions import IsAuthenticatedOrReadOnly

''' permissions.SAFE_METHODS is [GET] permissions.UNSAFE_METHODS are [POST, PUT, PATCH, DELETE]'''

class AdminOnly(permissions.BasePermission):
    """
    Allows access only to admin users.
    Allows admin to post and get to other users
    """
    message = 'Only admin users are allowed to perform this action. '
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        elif request.user.profile.role == 'admin':
            return  True
        else:
            return False
        
class IsRecieverProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.reciever_profile == request.user.profile
    
