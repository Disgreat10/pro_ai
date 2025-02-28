"""
Django settings for blackbox_trader project.
"""
import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'  # Change this in production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '.vscode.dev',
    '.github.dev',
    'fp3zfy-8000.csb.app',
    '*'  # Allow all hosts in development
]  # Configure this properly in production

# Security settings
CSRF_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None
CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = False

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'channels',
    'oauth2_provider',
    
    # Local apps
    'apps.users',
    'apps.analytics',
    'apps.trading',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.ActivityMonitoringMiddleware',
    'apps.users.middleware.LoginActivityMiddleware',
    'apps.users.middleware.SuspiciousActivityMiddleware',
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True

# Activity Monitoring Settings
ACTIVITY_MONITORING = {
    'FAILED_LOGIN_LIMIT': 5,  # Number of failed attempts before temporary block
    'BLOCK_DURATION': 300,    # Duration of block in seconds (5 minutes)
    'SUSPICIOUS_ACTIVITY_THRESHOLD': {
        'FAILED_LOGINS': 5,   # Number of failed logins to consider suspicious
        'TIME_WINDOW': 300,   # Time window in seconds (5 minutes)
    }
}

# Session Security Settings
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie

ROOT_URLCONF = 'blackbox_trader.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'apps/trading/templates'),
            os.path.join(BASE_DIR, 'apps/users/templates'),
            os.path.join(BASE_DIR, 'apps/users/templates/registration'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'blackbox_trader.wsgi.application'
ASGI_APPLICATION = 'blackbox_trader.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Static files storage with proper MIME type handling
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/trading/market-watch/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# CORS and CSRF settings
CORS_ALLOW_ALL_ORIGINS = True  # Configure this properly in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://fp3zfy-8000.csb.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'sec-websocket-protocol',
    'sec-websocket-version',
    'sec-websocket-extensions',
    'sec-websocket-key',
    'upgrade',
    'connection',
    'sec-websocket-accept'
]

CORS_EXPOSE_HEADERS = [
    'upgrade',
    'connection',
    'sec-websocket-accept'
]

WEBSOCKET_PROTOCOLS = [
    'wss',
    'ws'
]

WEBSOCKET_HANDSHAKE_TIMEOUT = 20  # seconds

WEBSOCKET_SUBPROTOCOLS = [
    'market.data.v1',  # For market data
    'trading.v1'       # For trading operations
]

WEBSOCKET_PING_INTERVAL = 30  # Send ping every 30 seconds to keep connection alive
WEBSOCKET_PING_TIMEOUT = 10   # Wait 10 seconds for pong response

# WebSocket error handling settings
WEBSOCKET_MAX_RETRIES = 5     # Maximum number of reconnection attempts
WEBSOCKET_RETRY_DELAY = 5     # Delay in seconds between reconnection attempts
WEBSOCKET_ERROR_THRESHOLD = 3  # Number of errors before forcing reconnection

# WebSocket logging settings
WEBSOCKET_LOG_LEVEL = 'INFO'  # Log level for WebSocket operations
WEBSOCKET_LOG_FILE = 'logs/websocket.log'  # File to store WebSocket logs
WEBSOCKET_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'  # Log format

# Additional logging settings
WEBSOCKET_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB max file size
WEBSOCKET_LOG_BACKUP_COUNT = 5  # Keep 5 backup files
WEBSOCKET_LOG_ENCODING = 'utf-8'  # Log file encoding

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

# WebSocket performance monitoring settings
WEBSOCKET_MONITOR_INTERVAL = 60  # Monitor stats every 60 seconds
WEBSOCKET_LATENCY_THRESHOLD = 1000  # Alert if latency exceeds 1000ms
WEBSOCKET_MESSAGE_RATE_THRESHOLD = 100  # Alert if message rate drops below 100/min
WEBSOCKET_MONITOR_LOG = 'logs/websocket_monitor.log'  # Performance monitoring log

# WebSocket alert notification settings
WEBSOCKET_ALERT_ENABLED = True  # Enable alert notifications
WEBSOCKET_ALERT_CHANNELS = ['log', 'email']  # Alert notification channels
WEBSOCKET_ALERT_EMAIL = 'admin@example.com'  # Email for alerts
WEBSOCKET_ALERT_COOLDOWN = 300  # Minimum seconds between alerts

# Alert severity levels
WEBSOCKET_ALERT_LEVELS = {
    'INFO': 0,      # Normal operations
    'WARNING': 1,   # Performance degradation
    'ERROR': 2,     # Connection issues
    'CRITICAL': 3   # Service disruption
}

# Severity thresholds for different metrics
WEBSOCKET_LATENCY_SEVERITY = {
    500: 'WARNING',    # >500ms latency
    1000: 'ERROR',     # >1s latency
    2000: 'CRITICAL'   # >2s latency
}

# Message rate severity thresholds (messages per minute)
WEBSOCKET_MESSAGE_RATE_SEVERITY = {
    100: 'WARNING',    # <100 messages/min
    50: 'ERROR',       # <50 messages/min
    10: 'CRITICAL'     # <10 messages/min
}

# Maximum time without messages before alert (seconds)
WEBSOCKET_SILENCE_THRESHOLD = 30

# Connection health monitoring settings
WEBSOCKET_HEALTH_CHECK_INTERVAL = 15  # Check connection every 15 seconds
WEBSOCKET_RECONNECT_ATTEMPTS = 3      # Number of reconnection attempts before critical alert
WEBSOCKET_RECONNECT_DELAY = 5         # Delay between reconnection attempts (seconds)
WEBSOCKET_PING_TIMEOUT = 10           # Timeout for ping/pong health check (seconds)

# Statistics collection settings
WEBSOCKET_STATS_WINDOW = 300          # Rolling window for stats collection (seconds)
WEBSOCKET_STATS_RESOLUTION = 10       # Resolution for latency measurements (milliseconds)
WEBSOCKET_STATS_BATCH_SIZE = 100      # Number of messages to batch before stats update
WEBSOCKET_STATS_LOG_INTERVAL = 60     # Interval to log statistics summary (seconds)

# Performance monitoring thresholds
WEBSOCKET_CPU_THRESHOLD = 80          # CPU usage threshold percentage
WEBSOCKET_MEMORY_THRESHOLD = 85       # Memory usage threshold percentage
WEBSOCKET_THREAD_THRESHOLD = 100      # Maximum number of websocket threads
WEBSOCKET_CONNECTION_THRESHOLD = 50    # Maximum concurrent connections

# Alert thresholds
WEBSOCKET_LATENCY_ALERT = 1000        # Alert if latency exceeds 1000ms
WEBSOCKET_ERROR_ALERT = 5             # Alert after 5 consecutive errors
WEBSOCKET_QUEUE_ALERT = 1000          # Alert if message queue exceeds 1000
WEBSOCKET_BACKLOG_ALERT = 100         # Alert if unprocessed messages exceed 100

# Logging configuration
WEBSOCKET_LOG_LEVEL = 'INFO'          # Log level for websocket operations
WEBSOCKET_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
WEBSOCKET_LOG_FILE = 'websocket.log'  # File to store websocket logs
WEBSOCKET_LOG_ROTATE = 5              # Number of log files to keep

# Path configuration
WEBSOCKET_LOG_DIR = 'logs/websocket'  # Directory for websocket logs
WEBSOCKET_STATS_DIR = 'logs/stats'    # Directory for statistics data
WEBSOCKET_DUMP_DIR = 'logs/dumps'     # Directory for message dumps

# Cleanup configuration
WEBSOCKET_LOG_CLEANUP_DAYS = 30       # Remove logs older than 30 days
WEBSOCKET_STATS_CLEANUP_DAYS = 90     # Remove stats older than 90 days
WEBSOCKET_DUMP_CLEANUP_DAYS = 7       # Remove dumps older than 7 days
WEBSOCKET_CLEANUP_TIME = '00:00'      # Time to run cleanup (24h format)

# Monitoring configuration
WEBSOCKET_MONITOR_INTERVAL = 60       # Monitor status every 60 seconds
WEBSOCKET_HEALTH_CHECK_URL = '/ws/health'  # Health check endpoint
WEBSOCKET_MONITOR_METRICS = [
    'connections',
    'messages_received',
    'messages_sent', 
    'errors',
    'latency'
]

# Notification configuration
WEBSOCKET_NOTIFY_EMAIL = True         # Enable email notifications
WEBSOCKET_NOTIFY_SLACK = False        # Enable Slack notifications
WEBSOCKET_NOTIFY_LEVELS = [
    'CRITICAL',                       # Severe errors requiring immediate attention
    'ERROR',                          # General errors
    'WARNING'                         # Potential issues
]
WEBSOCKET_NOTIFY_INTERVAL = 300       # Minimum time between notifications (seconds)

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.vscode.dev',
    'https://*.github.dev',
    'https://*.csb.app',
    'https://fp3zfy-8000.csb.app'
]

# Channels and WebSocket configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# WebSocket settings
ASGI_APPLICATION = 'blackbox_trader.asgi.application'
WEBSOCKET_ACCEPT_ALL = True  # Allow all WebSocket connections in development
CHANNEL_SECURITY = {
    'websocket': True
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    # 'handlers': {
    #     'file': {
    #         'level': 'DEBUG',
    #         'class': 'logging.FileHandler',
    #         'filename': os.path.join(BASE_DIR, 'debug.log'),
    #         'formatter': 'verbose',
    #     },
    # },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
