"""
URL configuration for blackbox_trader project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.users import urls as users_urls
from apps.trading import urls as trading_urls

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # JWT authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OAuth2
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    
    # API endpoints
    path('api/users/', include((users_urls.api_patterns, 'users-api'))),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/trading/', include((trading_urls.api_patterns, 'trading-api'))),

    # Frontend views
    path('trading/', include((trading_urls.urlpatterns, 'trading'))),
    
    # Authentication views
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
