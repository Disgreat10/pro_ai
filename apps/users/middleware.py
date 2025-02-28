import json
from django.utils import timezone
from .models import LoginHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class ActivityMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        if request.user.is_authenticated:
            # Update last active timestamp
            User.objects.filter(pk=request.user.pk).update(
                last_active=timezone.now(),
                last_login_ip=self.get_client_ip(request)
            )

            # Update device info if changed
            current_device_info = self.get_device_info(request)
            if current_device_info != request.user.device_info:
                User.objects.filter(pk=request.user.pk).update(
                    device_info=current_device_info
                )

        response = self.get_response(request)

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_device_info(self, request):
        device_info = {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
            'mobile': request.META.get('HTTP_SEC_CH_UA_MOBILE', ''),
            'browser': request.META.get('HTTP_SEC_CH_UA', '')
        }
        return device_info

class LoginActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Track successful logins
        if (
            request.path == '/admin/login/' 
            and request.method == 'POST' 
            and response.status_code == 302
            and request.user.is_authenticated
        ):
            LoginHistory.objects.create(
                user=request.user,
                ip_address=self.get_client_ip(request),
                device_info=self.get_device_info(request),
                status='SUCCESS',
                location_info=self.get_location_info(request)
            )
        
        # Track failed login attempts
        elif (
            request.path == '/admin/login/' 
            and request.method == 'POST' 
            and response.status_code == 200
        ):
            # Try to get username from POST data
            username = request.POST.get('username', '')
            try:
                user = User.objects.get(username=username)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=self.get_client_ip(request),
                    device_info=self.get_device_info(request),
                    status='FAILED',
                    location_info=self.get_location_info(request)
                )
            except User.DoesNotExist:
                pass

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_device_info(self, request):
        return {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
            'mobile': request.META.get('HTTP_SEC_CH_UA_MOBILE', ''),
            'browser': request.META.get('HTTP_SEC_CH_UA', '')
        }

    def get_location_info(self, request):
        # In a production environment, you would use a geolocation service
        # For now, we'll return basic info from headers
        return {
            'country': request.META.get('HTTP_CF_IPCOUNTRY', ''),
            'city': '',
            'timezone': request.META.get('TZ', '')
        }

class SuspiciousActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.failed_attempts = {}

    def __call__(self, request):
        response = self.get_response(request)

        # Check for suspicious activities
        ip_address = self.get_client_ip(request)
        
        # Track failed login attempts
        if (
            request.path == '/admin/login/' 
            and request.method == 'POST' 
            and response.status_code == 200
        ):
            self.failed_attempts.setdefault(ip_address, {
                'count': 0,
                'first_attempt': timezone.now()
            })
            self.failed_attempts[ip_address]['count'] += 1

            # Check if we should block this IP
            if self.should_block_ip(ip_address):
                # In production, you would implement IP blocking here
                # For now, we'll just log it
                print(f"Suspicious activity detected from IP: {ip_address}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def should_block_ip(self, ip_address):
        if ip_address not in self.failed_attempts:
            return False

        attempts = self.failed_attempts[ip_address]
        time_window = timezone.now() - attempts['first_attempt']
        
        # Block if more than 5 failed attempts within 5 minutes
        if attempts['count'] >= 5 and time_window.total_seconds() <= 300:
            return True

        # Reset counter if outside time window
        if time_window.total_seconds() > 300:
            self.failed_attempts[ip_address] = {
                'count': 0,
                'first_attempt': timezone.now()
            }

        return False
