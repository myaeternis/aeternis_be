"""
Django Dev Settings - For shared development environment.

Usage: DJANGO_SETTINGS_MODULE=config.settings.dev
Branch: develop
"""

from .base import *

# SECURITY
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# Database - PostgreSQL for dev environment
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# CORS Configuration
FRONTEND_URL = config('FRONTEND_URL')
CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
]
CORS_ALLOW_CREDENTIALS = True

# Security settings (relaxed for dev)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email - Use console or SMTP
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

# Logging
LOGGING['loggers']['django']['level'] = 'DEBUG'

print("🔨 Using DEV settings")
