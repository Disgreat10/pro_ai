from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker

class User(AbstractUser):
    """
    Custom User model for blackbox trader platform.
    Extends Django's AbstractUser to add trading-specific fields.
    """
    tracker = FieldTracker()
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MODERATOR = 'MODERATOR', _('Moderator')
        USER = 'USER', _('User')

    # Basic profile fields
    role = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.USER
    )
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # KYC verification fields
    is_kyc_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(max_length=20, default='PENDING')
    kyc_submitted_at = models.DateTimeField(null=True, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Activity monitoring fields
    last_active = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    
    # Trading related fields
    trading_status = models.CharField(max_length=20, default='ACTIVE')
    trading_level = models.CharField(max_length=20, default='BEGINNER')
    trading_volume = models.DecimalField(
        max_digits=20, 
        decimal_places=8, 
        default=0
    )
    
    # Security and activity tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    
    # Referral system
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='referrals'
    )
    referral_earnings = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0
    )
    
    # Account status and restrictions
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspension_start = models.DateTimeField(null=True, blank=True)
    suspension_end = models.DateTimeField(null=True, blank=True)
    
    # Risk management
    risk_level = models.CharField(max_length=20, default='NORMAL')
    daily_withdrawal_limit = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0
    )
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def __str__(self):
        return self.username
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    def suspend_account(self, reason, end_date=None):
        """Suspend user account with reason and optional end date."""
        from django.utils import timezone
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspension_start = timezone.now()
        self.suspension_end = end_date
        self.save()
        
    def activate_account(self):
        """Reactivate suspended account."""
        self.is_suspended = False
        self.suspension_reason = ''
        self.suspension_start = None
        self.suspension_end = None
        self.save()
        
    def update_trading_volume(self, amount):
        """Update user's trading volume."""
        self.trading_volume += amount
        self.save()
        
    def update_risk_level(self, new_level):
        """Update user's risk level and adjust limits accordingly."""
        self.risk_level = new_level
        # Implement risk-based limit adjustments here
        self.save()

class LoginHistory(models.Model):
    """Track user login attempts and sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    device_info = models.JSONField()
    status = models.CharField(max_length=20)  # SUCCESS, FAILED, BLOCKED
    location_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-login_time']
        
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"

class KYCDocument(models.Model):
    """Store KYC document information."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=50)
    document_number = models.CharField(max_length=50)
    document_file = models.FileField(upload_to='kyc_documents/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    verification_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.document_type}"
