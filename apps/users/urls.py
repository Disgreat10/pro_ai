from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'kyc', views.KYCDocumentViewSet, basename='kyc')
router.register(r'login-history', views.LoginHistoryViewSet, basename='login-history')
router.register(r'referrals', views.ReferralViewSet, basename='referral')

# API URLs
api_patterns = [
    path('', include(router.urls)),
]

# Frontend URLs
urlpatterns = [
    path('login/', views.login_view, name='login'),
]
