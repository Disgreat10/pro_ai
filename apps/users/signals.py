from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import Group
from .models import User, KYCDocument
from .permissions import setup_role_permissions

@receiver(post_save, sender=User)
def handle_user_role_change(sender, instance, created, raw, **kwargs):
    """
    Handle permission assignments when a user is created or role is changed.
    """
    if raw:  # Skip during loaddata
        return

    # Ensure role-based permissions are set up
    if created and instance.is_superuser:
        # For the first superuser, set up all permission groups
        setup_role_permissions()
    
    # Get or create the appropriate group based on role
    if instance.role == User.RoleChoices.ADMIN:
        group = Group.objects.get_or_create(name='Admin')[0]
        instance.is_staff = True
        instance.is_superuser = True
    elif instance.role == User.RoleChoices.MODERATOR:
        group = Group.objects.get_or_create(name='Moderator')[0]
        instance.is_staff = True
        instance.is_superuser = False
    else:
        group = Group.objects.get_or_create(name='User')[0]
        instance.is_staff = False
        instance.is_superuser = False

    # Update groups without triggering save
    instance.groups.set([group])
    
    # Update is_staff and is_superuser without triggering save
    if instance.tracker.has_changed('is_staff') or instance.tracker.has_changed('is_superuser'):
        User.objects.filter(pk=instance.pk).update(
            is_staff=instance.is_staff,
            is_superuser=instance.is_superuser
        )

@receiver(pre_save, sender=User)
def handle_user_status_change(sender, instance, **kwargs):
    """
    Handle user status changes and logging.
    """
    if not instance.pk:  # New user
        return
    
    old_instance = User.objects.get(pk=instance.pk)
    
    # Handle suspension status change
    if instance.is_suspended != old_instance.is_suspended:
        if instance.is_suspended:
            instance.suspension_start = timezone.now()
            if not instance.suspension_reason:
                instance.suspension_reason = "Administrative action"
        else:
            instance.suspension_start = None
            instance.suspension_end = None
            instance.suspension_reason = ""

@receiver(post_save, sender=KYCDocument)
def handle_kyc_verification(sender, instance, created, **kwargs):
    """
    Update user's KYC status when documents are verified.
    """
    if not created and instance.status in ['APPROVED', 'REJECTED']:
        user = instance.user
        user.kyc_status = instance.status
        user.is_kyc_verified = (instance.status == 'APPROVED')
        if instance.status == 'APPROVED':
            user.kyc_verified_at = timezone.now()
        user.save()
