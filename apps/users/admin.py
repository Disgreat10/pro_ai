from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, LoginHistory, KYCDocument

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'trading_status', 'account_status', 'kyc_status', 'last_active', 'last_login_ip')
    list_filter = ('role', 'trading_status', 'is_suspended', 'kyc_status', 'trading_level', 'risk_level', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'last_login_ip')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'email', 'password', 'role')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')
        }),
        ('Trading Profile', {
            'fields': ('trading_status', 'trading_level', 'trading_volume', 'risk_level', 'daily_withdrawal_limit')
        }),
        ('KYC Information', {
            'fields': ('is_kyc_verified', 'kyc_status', 'kyc_submitted_at', 'kyc_verified_at')
        }),
        ('Activity Monitoring', {
            'fields': ('last_login', 'last_active', 'last_login_ip', 'device_info', 'failed_login_attempts', 'last_failed_login')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_suspended', 'suspension_reason', 'suspension_start', 'suspension_end')
        }),
        ('Security', {
            'fields': ('two_factor_enabled',)
        }),
        ('Referral Information', {
            'fields': ('referral_code', 'referred_by', 'referral_earnings')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = (
        'last_login', 'date_joined', 'last_active', 'last_login_ip', 'referral_earnings',
        'failed_login_attempts', 'last_failed_login', 'device_info'
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    
    def account_status(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: red;">Inactive</span>')
        if obj.is_suspended:
            if obj.suspension_end and obj.suspension_end > timezone.now():
                return format_html(
                    '<span style="color: orange;">Suspended until {}</span>',
                    obj.suspension_end.strftime('%Y-%m-%d')
                )
            return format_html('<span style="color: red;">Suspended</span>')
        if obj.failed_login_attempts > 3:
            return format_html('<span style="color: orange;">Login Attempts: {}</span>', obj.failed_login_attempts)
        return format_html('<span style="color: green;">Active</span>')
    
    account_status.short_description = 'Status'

    actions = ['suspend_accounts', 'activate_accounts', 'enable_2fa', 'disable_2fa', 'reset_failed_logins']

    def suspend_accounts(self, request, queryset):
        queryset.update(
            is_suspended=True,
            suspension_start=timezone.now(),
            suspension_reason='Administrative action'
        )
    suspend_accounts.short_description = "Suspend selected accounts"

    def activate_accounts(self, request, queryset):
        queryset.update(
            is_suspended=False,
            suspension_reason='',
            suspension_start=None,
            suspension_end=None
        )
    activate_accounts.short_description = "Activate selected accounts"

    def enable_2fa(self, request, queryset):
        queryset.update(two_factor_enabled=True)
    enable_2fa.short_description = "Enable 2FA for selected accounts"

    def disable_2fa(self, request, queryset):
        queryset.update(two_factor_enabled=False)
    disable_2fa.short_description = "Disable 2FA for selected accounts"

    def reset_failed_logins(self, request, queryset):
        queryset.update(failed_login_attempts=0, last_failed_login=None)
    reset_failed_logins.short_description = "Reset failed login attempts"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.role != 'ADMIN':
            return []  # Non-admin users can't perform bulk actions
        return actions

    def get_readonly_fields(self, request, obj=None):
        if request.user.role != 'ADMIN':
            # Non-admin users can't change critical fields
            return self.readonly_fields + ('is_staff', 'is_superuser', 'groups', 'user_permissions', 'role')
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'ADMIN'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'ADMIN':
            return qs
        elif request.user.role == 'MODERATOR':
            return qs.exclude(role='ADMIN')  # Moderators can't see admin users
        return qs.filter(id=request.user.id)  # Regular users can only see themselves

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'status', 'location_info_display', 'device_info_display')
    list_filter = ('status', 'login_time', 'user')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_time',)
    readonly_fields = ('user', 'login_time', 'ip_address', 'device_info', 'status', 'location_info')
    
    def location_info_display(self, obj):
        if not obj.location_info:
            return '-'
        return format_html(
            '{city}, {country}',
            city=obj.location_info.get('city', 'Unknown'),
            country=obj.location_info.get('country', 'Unknown')
        )
    location_info_display.short_description = 'Location'

    def device_info_display(self, obj):
        if not obj.device_info:
            return '-'
        return format_html(
            '{}<br>Platform: {}<br>Browser: {}',
            obj.device_info.get('user_agent', 'Unknown'),
            obj.device_info.get('platform', 'Unknown'),
            obj.device_info.get('browser', 'Unknown')
        )
    device_info_display.short_description = 'Device Info'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'ADMIN'

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'ADMIN':
            return qs
        elif request.user.role == 'MODERATOR':
            return qs.filter(status='FAILED')  # Moderators can only see failed attempts
        return qs.filter(user=request.user)  # Regular users can only see their own history

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'submitted_at', 'verified_at', 'document_preview')
    list_filter = ('status', 'document_type', 'submitted_at')
    search_fields = ('user__username', 'document_number')
    ordering = ('-submitted_at',)
    
    def document_preview(self, obj):
        if obj.document_file:
            return format_html(
                '<a href="{}" target="_blank">View Document</a>',
                obj.document_file.url
            )
        return '-'
    document_preview.short_description = 'Document'

    actions = ['approve_documents', 'reject_documents']

    def approve_documents(self, request, queryset):
        queryset.update(
            status='APPROVED',
            verified_at=timezone.now()
        )
        # Update user KYC status
        for doc in queryset:
            user = doc.user
            user.is_kyc_verified = True
            user.kyc_status = 'APPROVED'
            user.kyc_verified_at = timezone.now()
            user.save()
    approve_documents.short_description = "Approve selected documents"

    def reject_documents(self, request, queryset):
        queryset.update(
            status='REJECTED',
            verified_at=timezone.now()
        )
        # Update user KYC status
        for doc in queryset:
            user = doc.user
            user.is_kyc_verified = False
            user.kyc_status = 'REJECTED'
            user.save()
    reject_documents.short_description = "Reject selected documents"
