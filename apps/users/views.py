from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model, login, authenticate
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import LoginHistory, KYCDocument
from .serializers import (
    UserSerializer, UserCreateSerializer, UserDetailSerializer,
    UserUpdateSerializer, AdminUserUpdateSerializer, KYCDocumentSerializer,
    LoginHistorySerializer, ChangePasswordSerializer, Enable2FASerializer,
    ReferralSerializer
)
from .permissions import IsUserOrAdmin, IsModeratorOrAdmin

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Record successful login
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                device_info=request.META.get('HTTP_USER_AGENT', ''),
                status='SUCCESS'
            )
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('trading:market-watch')
        else:
            # Record failed login attempt if user exists
            if username:
                user = User.objects.filter(username=username).first()
                if user:
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        device_info=request.META.get('HTTP_USER_AGENT', ''),
                        status='FAILED'
                    )
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'registration/login.html')

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling user-related operations.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            if self.request.user.role == 'ADMIN':
                return AdminUserUpdateSerializer
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            return [IsUserOrAdmin()]
        return [IsModeratorOrAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Record login history
        LoginHistory.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            device_info=request.META.get('HTTP_USER_AGENT', ''),
            status='SUCCESS'
        )
        
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.data['old_password']):
                return Response(
                    {'error': 'Invalid old password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user.set_password(serializer.data['new_password'])
            user.save()
            return Response({'status': 'password changed'})
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def enable_2fa(self, request, pk=None):
        user = self.get_object()
        serializer = Enable2FASerializer(data=request.data)
        
        if serializer.is_valid():
            user.two_factor_enabled = True
            user.save()
            return Response({'status': '2FA enabled'})
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def suspend_account(self, request, pk=None):
        user = self.get_object()
        if not request.user.role == 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user.suspend_account(
            reason=request.data.get('reason'),
            end_date=request.data.get('end_date')
        )
        return Response({'status': 'account suspended'})

    @action(detail=True, methods=['post'])
    def activate_account(self, request, pk=None):
        user = self.get_object()
        if not request.user.role == 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user.activate_account()
        return Response({'status': 'account activated'})

class KYCDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling KYC document operations.
    """
    serializer_class = KYCDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role in ['ADMIN', 'MODERATOR']:
            return KYCDocument.objects.all()
        return KYCDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsModeratorOrAdmin])
    def verify(self, request, pk=None):
        document = self.get_object()
        document.status = 'VERIFIED'
        document.verified_at = timezone.now()
        document.verification_notes = request.data.get('notes', '')
        document.save()
        
        # Update user's KYC status
        user = document.user
        user.is_kyc_verified = True
        user.kyc_verified_at = timezone.now()
        user.save()
        
        return Response({'status': 'document verified'})

class LoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing login history.
    """
    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return LoginHistory.objects.all()
        return LoginHistory.objects.filter(user=self.request.user)

class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for handling referral-related operations.
    """
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(referred_by=self.request.user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        referrals = self.get_queryset()
        total_referrals = referrals.count()
        total_earnings = sum(ref.referral_earnings for ref in referrals)
        active_referrals = referrals.filter(trading_status='ACTIVE').count()
        
        return Response({
            'total_referrals': total_referrals,
            'total_earnings': total_earnings,
            'active_referrals': active_referrals
        })
