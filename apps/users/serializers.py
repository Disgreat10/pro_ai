from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LoginHistory, KYCDocument

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Base serializer for User model."""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'date_of_birth', 'is_kyc_verified',
            'kyc_status', 'trading_status', 'trading_level',
            'trading_volume', 'two_factor_enabled', 'referral_code',
            'is_suspended', 'risk_level', 'daily_withdrawal_limit'
        ]
        read_only_fields = [
            'trading_volume', 'is_kyc_verified', 'kyc_status',
            'risk_level', 'daily_withdrawal_limit'
        ]

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 'date_of_birth'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserDetailSerializer(UserSerializer):
    """Detailed user serializer including related data."""
    referral_count = serializers.SerializerMethodField()
    total_referral_earnings = serializers.DecimalField(
        max_digits=20, decimal_places=8, read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'referral_count', 'total_referral_earnings',
            'last_login_ip', 'last_active'
        ]

    def get_referral_count(self, obj):
        return obj.referrals.count()

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'date_of_birth'
        ]

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin-level user updates."""
    class Meta:
        model = User
        fields = [
            'role', 'trading_status', 'trading_level',
            'is_suspended', 'suspension_reason', 'suspension_end',
            'risk_level', 'daily_withdrawal_limit'
        ]

class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC documents."""
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'document_type', 'document_number',
            'document_file', 'submitted_at', 'verified_at',
            'status', 'verification_notes'
        ]
        read_only_fields = ['verified_at', 'status', 'verification_notes']

class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login history."""
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'login_time', 'ip_address',
            'device_info', 'status', 'location_info'
        ]
        read_only_fields = fields

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA."""
    verification_code = serializers.CharField(required=True)

class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for referral information."""
    referred_user = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'referred_user', 'referral_earnings',
            'trading_volume', 'trading_status'
        ]
