"""
Django Staging Settings - For QA/validation environment.

Usage: DJANGO_SETTINGS_MODULE=config.settings.staging
Branch: staging
"""

from .base import *

# SECURITY
SECRET_KEY = config('SECRET_KEY')
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Database - PostgreSQL for staging
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

# CORS Configuration
FRONTEND_URL = config('FRONTEND_URL')
CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
]
CORS_ALLOW_CREDENTIALS = True

# Security settings (production-like but with some relaxation)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (shorter duration for staging)
SECURE_HSTS_SECONDS = 3600  # 1 hour
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

# Email
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Logging - More verbose for debugging in staging
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['payments']['level'] = 'DEBUG'
LOGGING['loggers']['orders']['level'] = 'DEBUG'

print("🧪 Using STAGING settings")
