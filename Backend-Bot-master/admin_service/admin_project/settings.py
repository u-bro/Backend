import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-test-key-for-admin-service')

DEBUG = os.getenv('DJANGO_DEBUG', '0') in {'1', 'true', 'True', 'yes', 'YES'}

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'api.dev.u-bro.ru']

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
    'admin_tariffs.apps.AdminTariffsConfig',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "Admin Panel",
    "site_header": "Admin Panel",
    "site_brand": "Admin",
    "welcome_sign": "Добро пожаловать в админ панель",
}

CSRF_TRUSTED_ORIGINS = [
    'https://api.dev.u-bro.ru',
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
