from .base import *
import os

DEBUG = False

# Override settings for Vercel deployment
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']

# Use SQLite for now if no proper database is configured
if os.getenv('DB_NAME') == 'placeholder' or not os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Disable database-dependent features for now
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'django_celery' not in app]

# Simplified middleware for Vercel
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Static files configuration for Vercel
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
