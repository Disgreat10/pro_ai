from rest_framework import permissions
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User

class IsAdmin(permissions.BasePermission):
    """
    Permission check for Admin role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == User.RoleChoices.ADMIN

class IsModerator(permissions.BasePermission):
    """
    Permission check for Moderator role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == User.RoleChoices.MODERATOR

class IsModeratorOrAdmin(permissions.BasePermission):
    """
    Permission check for Admin or Moderator role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role in [
            User.RoleChoices.ADMIN,
            User.RoleChoices.MODERATOR
        ]

class IsUserOrAdmin(permissions.BasePermission):
    """
    Permission check for User's own data or Admin.
    """
    def has_permission(self, request, view):
        return request.user and (
            request.user.role == User.RoleChoices.ADMIN or
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return request.user and (
            request.user.role == User.RoleChoices.ADMIN or
            obj.id == request.user.id
        )

def setup_role_permissions():
    """
    Set up default permissions for different roles.
    This should be run after migrations.
    """
    # Create default groups if they don't exist
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    moderator_group, _ = Group.objects.get_or_create(name='Moderator')
    user_group, _ = Group.objects.get_or_create(name='User')

    # Get content types for our models
    user_ct = ContentType.objects.get_for_model(User)
    
    # Define permissions for each role
    admin_permissions = Permission.objects.all()
    
    moderator_permissions = Permission.objects.filter(
        content_type__in=[user_ct],
        codename__in=[
            'view_user',
            'change_user',
            'view_kycdocument',
            'change_kycdocument',
            'view_loginhistory',
            'view_analytics',
            'view_tradingdata',
        ]
    )
    
    user_permissions = Permission.objects.filter(
        content_type__in=[user_ct],
        codename__in=[
            'view_user',
            'view_analytics',
        ]
    )

    # Assign permissions to groups
    admin_group.permissions.set(admin_permissions)
    moderator_group.permissions.set(moderator_permissions)
    user_group.permissions.set(user_permissions)

def assign_role_permissions(user):
    """
    Assign appropriate permissions based on user's role.
    This should be called when a user's role changes.
    """
    # Remove user from all role groups first
    user.groups.clear()
    
    # Assign to appropriate group based on role
    if user.role == User.RoleChoices.ADMIN:
        admin_group = Group.objects.get(name='Admin')
        user.groups.add(admin_group)
        user.is_staff = True
        user.is_superuser = True
    
    elif user.role == User.RoleChoices.MODERATOR:
        moderator_group = Group.objects.get(name='Moderator')
        user.groups.add(moderator_group)
        user.is_staff = True
        user.is_superuser = False
    
    else:  # Regular user
        user_group = Group.objects.get(name='User')
        user.groups.add(user_group)
        user.is_staff = False
        user.is_superuser = False
    
    user.save()

# Permission sets for different views/actions
ADMIN_PERMISSIONS = {
    'user_management': [
        'add_user',
        'change_user',
        'delete_user',
        'view_user',
        'suspend_user',
        'activate_user',
    ],
    'kyc_management': [
        'approve_kyc',
        'reject_kyc',
        'view_kycdocument',
    ],
    'analytics': [
        'view_analytics',
        'export_analytics',
        'configure_analytics',
    ],
    'system': [
        'configure_system',
        'view_logs',
        'manage_permissions',
    ],
}

MODERATOR_PERMISSIONS = {
    'user_management': [
        'view_user',
        'change_user',
        'suspend_user',
    ],
    'kyc_management': [
        'view_kycdocument',
        'approve_kyc',
        'reject_kyc',
    ],
    'analytics': [
        'view_analytics',
        'export_analytics',
    ],
}

USER_PERMISSIONS = {
    'user_management': [
        'view_user',
    ],
    'analytics': [
        'view_analytics',
    ],
}

def check_permission(user, permission_name):
    """
    Check if a user has a specific permission based on their role.
    """
    if user.role == User.RoleChoices.ADMIN:
        # Admins have all permissions
        return True
    
    elif user.role == User.RoleChoices.MODERATOR:
        # Check if permission exists in moderator permissions
        for category in MODERATOR_PERMISSIONS.values():
            if permission_name in category:
                return True
        return False
    
    else:  # Regular user
        # Check if permission exists in user permissions
        for category in USER_PERMISSIONS.values():
            if permission_name in category:
                return True
        return False
