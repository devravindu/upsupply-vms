"""
Django settings for core project.
"""

import importlib.util
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'insecure-dev-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [host for host in os.getenv('ALLOWED_HOSTS', '*').split(',') if host]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'management',
]

if importlib.util.find_spec('django_otp'):
    INSTALLED_APPS += [
        'django_otp',
        'django_otp.plugins.otp_totp',
        'django_otp.plugins.otp_static',
    ]
if importlib.util.find_spec('two_factor'):
    INSTALLED_APPS.append('two_factor')
if importlib.util.find_spec('rest_framework'):
    INSTALLED_APPS.append('rest_framework')
if importlib.util.find_spec('storages'):
    INSTALLED_APPS.append('storages')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


if importlib.util.find_spec('django_otp'):
    MIDDLEWARE.insert(5, 'django_otp.middleware.OTPMiddleware')
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'


def _database_from_url(database_url):
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)
    ssl_mode = query.get('sslmode', ['require'])[0]

    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path.lstrip('/'),
        'USER': parsed.username,
        'PASSWORD': parsed.password,
        'HOST': parsed.hostname,
        'PORT': str(parsed.port or '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {'sslmode': ssl_mode},
    }


DATABASE_URL = os.getenv('DATABASE_URL')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
if DATABASE_URL:
    DATABASES = {'default': _database_from_url(DATABASE_URL)}
elif ENVIRONMENT in {'production', 'staging'}:
    raise RuntimeError('DATABASE_URL must be configured with a PostgreSQL connection in production/staging.')
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

LOGIN_REDIRECT_URL = '/vendor/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = 'two_factor:login' if importlib.util.find_spec('two_factor') else '/accounts/login/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local').lower()
if STORAGE_BACKEND == 's3':
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', '')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
elif STORAGE_BACKEND == 'gcs':
    GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', '')
    GS_DEFAULT_ACL = None
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_BEAT_SCHEDULE = {
    'run-certification-expiry-checks-daily': {
        'task': 'management.tasks.run_daily_certification_checks',
        'schedule': 60 * 60 * 24,
    }
}

if importlib.util.find_spec('rest_framework'):
    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
