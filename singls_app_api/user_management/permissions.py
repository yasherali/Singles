from rest_framework import permissions
from user_management.models import Profile

class IsUser(permissions.BasePermission):
    message = 'Only authenticated users are allowed to perform this action.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and Profile.objects.filter(user=request.user).exists()
    
class IsAdmin(permissions.BasePermission):
    message = 'Only admin users are allowed to perform this action. '
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser