from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.users.models import User, KYCDocument, LoginHistory
from apps.analytics.models import (
    TradeAnalytics, RevenueReport, RiskExposure,
    ProfitLoss, CustomReport, AnalyticsSnapshot,
    MarketPrediction, SentimentAnalysis, SystemHealth
)

class Command(BaseCommand):
    help = 'Set up initial roles and permissions for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up roles and permissions...')

        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        moderator_group, _ = Group.objects.get_or_create(name='Moderator')
        user_group, _ = Group.objects.get_or_create(name='User')

        # Get content types for all relevant models
        user_ct = ContentType.objects.get_for_model(User)
        kyc_ct = ContentType.objects.get_for_model(KYCDocument)
        login_ct = ContentType.objects.get_for_model(LoginHistory)
        
        # Analytics content types
        analytics_cts = [
            ContentType.objects.get_for_model(model) for model in [
                TradeAnalytics, RevenueReport, RiskExposure,
                ProfitLoss, CustomReport, AnalyticsSnapshot,
                MarketPrediction, SentimentAnalysis, SystemHealth
            ]
        ]

        # Set up admin permissions (all permissions)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(self.style.SUCCESS('Admin permissions set up'))

        # Set up moderator permissions
        moderator_permissions = []
        
        # User management permissions for moderators
        moderator_permissions.extend(Permission.objects.filter(
            content_type=user_ct,
            codename__in=['view_user', 'change_user']
        ))

        # KYC management permissions for moderators
        moderator_permissions.extend(Permission.objects.filter(
            content_type=kyc_ct,
            codename__in=['view_kycdocument', 'change_kycdocument']
        ))

        # Login history viewing for moderators
        moderator_permissions.extend(Permission.objects.filter(
            content_type=login_ct,
            codename='view_loginhistory'
        ))

        # Analytics permissions for moderators
        for ct in analytics_cts:
            moderator_permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=['view_' + ct.model, 'change_' + ct.model]
            ))

        moderator_group.permissions.set(moderator_permissions)
        self.stdout.write(self.style.SUCCESS('Moderator permissions set up'))

        # Set up regular user permissions
        user_permissions = []
        
        # Basic user permissions
        user_permissions.extend(Permission.objects.filter(
            content_type=user_ct,
            codename='view_user'
        ))

        # Basic analytics viewing permissions
        for ct in analytics_cts:
            user_permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename='view_' + ct.model
            ))

        user_group.permissions.set(user_permissions)
        self.stdout.write(self.style.SUCCESS('User permissions set up'))

        # Update existing users' permissions based on their roles
        for user in User.objects.all():
            if user.role == User.RoleChoices.ADMIN:
                user.groups.set([admin_group])
                user.is_staff = True
                user.is_superuser = True
            elif user.role == User.RoleChoices.MODERATOR:
                user.groups.set([moderator_group])
                user.is_staff = True
                user.is_superuser = False
            else:
                user.groups.set([user_group])
                user.is_staff = False
                user.is_superuser = False
            user.save()

        self.stdout.write(self.style.SUCCESS('Successfully set up all roles and permissions'))
