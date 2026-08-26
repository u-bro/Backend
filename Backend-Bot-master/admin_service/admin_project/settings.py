import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-test-key-for-admin-service')

DEBUG = os.getenv('DJANGO_DEBUG', '0') in {'1', 'true', 'True', 'yes', 'YES'}

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'api.dev.u-bro.ru', 'u-bro.ru']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'admin_users.apps.AdminUsersConfig',
    'admin_drivers.apps.AdminDriversConfig',
    'admin_rides.apps.AdminRidesConfig',
    'admin_roles.apps.AdminRolesConfig',
    'admin_driver_documents.apps.AdminDriverDocumentsConfig',
    'admin_chat_messages.apps.AdminChatMessagesConfig',
    'admin_commissions.apps.AdminCommissionsConfig',
    'admin_commission_payments.apps.AdminCommissionPaymentsConfig',
    'admin_ride_status_history.apps.AdminRideStatusHistoryConfig',
    'admin_cars.apps.AdminCarsConfig',
    'admin_car_photos.apps.AdminCarPhotosConfig',
    'admin_driver_locations.apps.AdminDriverLocationsConfig',
    'admin_ride_drivers_requests.apps.AdminRideDriversRequestsConfig',
    'admin_support.apps.AdminSupportConfig',
    'admin_push_notifications.apps.AdminPushNotificationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'admin_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_drivers.context_processors.moderation_queue',
            ],
        },
    },
]

WSGI_APPLICATION = 'admin_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASS', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=admin_public,public'
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

SUPPORT_API_BASE_URL = os.getenv('SUPPORT_API_BASE_URL', 'http://fastapi_app:5000')
SUPPORT_API_TIMEOUT = int(os.getenv('SUPPORT_API_TIMEOUT', '10'))
PUSH_API_BASE_URL = os.getenv('PUSH_API_BASE_URL', SUPPORT_API_BASE_URL)
PUSH_API_TIMEOUT = int(os.getenv('PUSH_API_TIMEOUT', '120'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

JAZZMIN_SETTINGS = {
    "site_title": "Admin Panel",
    "site_header": "Admin Panel",
    "site_brand": "Admin",
    "welcome_sign": "Добро пожаловать в админ панель",
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Модерация водителей", "url": "driver-moderation-list"},
        {"name": "Поддержка", "url": "support-workspace", "permissions": ["admin_support.view_supportconversation"]},
        {"name": "Политики", "url": "admin-policies", "permissions": ["auth.view_user"]},
    ],
    "hide_apps": [
        "admin_users",
        "admin_driver_documents",
        "admin_commissions",
        "admin_commission_payments",
        "admin_ride_status_history",
        "admin_cars",
        "admin_car_photos",
        "admin_driver_locations",
        "admin_ride_drivers_requests",
    ],
    "hide_models": [
        "auth.User",
        "admin_drivers.DriverProfileModeration",
        "admin_drivers.DriverModerationInfo",
    ],
    "custom_links": {
        "auth": [
            {"name": "Администраторы", "url": "admin:auth_user_changelist", "icon": "fas fa-user-shield", "permissions": ["auth.view_user"]},
            {"name": "Пользователи", "url": "admin:admin_users_user_changelist", "icon": "fas fa-users", "permissions": ["admin_users.view_user"]},
        ],
        "admin_drivers": [
            {"name": "Автомобили", "url": "admin:admin_cars_car_changelist", "icon": "fas fa-car", "permissions": ["admin_cars.view_car"]},
            {"name": "Локации водителей", "url": "admin:admin_driver_locations_driverlocation_changelist", "icon": "fas fa-map-marker-alt", "permissions": ["admin_driver_locations.view_driverlocation"]},
            {"name": "Причины модераций", "url": "admin:admin_drivers_drivermoderationinfo_changelist", "icon": "fas fa-clipboard-list", "permissions": ["admin_drivers.view_drivermoderationinfo"]},
        ],
        "admin_rides": [
            {"name": "Платежи комиссий", "url": "admin:admin_commission_payments_commissionpayment_changelist", "icon": "fas fa-credit-card", "permissions": ["admin_commission_payments.view_commissionpayment"]},
            {"name": "Комиссии", "url": "admin:admin_commissions_commission_changelist", "icon": "fas fa-percent", "permissions": ["admin_commissions.view_commission"]},
            {"name": "Истории статусов поездок", "url": "admin:admin_ride_status_history_ridestatushistory_changelist", "icon": "fas fa-history", "permissions": ["admin_ride_status_history.view_ridestatushistory"]},
            {"name": "Запросы водителей", "url": "admin:admin_ride_drivers_requests_ridedriversrequest_changelist", "icon": "fas fa-route", "permissions": ["admin_ride_drivers_requests.view_ridedriversrequest"]},
        ],
    },
    "order_with_respect_to": [
        "auth",
        "admin_drivers",
        "admin_rides",
        "admin_chat_messages",
        "admin_roles",
        "axes",
    ],
    "custom_css": "admin_support/support.css",
    "custom_js": "admin_support/support.js",
}

CSRF_TRUSTED_ORIGINS = [
    'https://api.dev.u-bro.ru',
    'https://u-bro.ru'
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', '5'))
AXES_COOLOFF_TIME = int(os.getenv('AXES_COOLOFF_TIME', '1'))
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
AXES_ONLY_USER_FAILURES = False
AXES_LOCKOUT_TEMPLATE = None

DRIVER_PROFILE_INITIAL_RATING_AVG = float(os.getenv('DRIVER_PROFILE_INITIAL_RATING_AVG', '5.0'))
DRIVER_PROFILE_INITIAL_RATING_COUNT = int(os.getenv('DRIVER_PROFILE_INITIAL_RATING_COUNT', '10'))
