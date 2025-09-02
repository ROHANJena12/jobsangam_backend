"""
Django settings for backend project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("true", "1")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# -------------------------------------------------------------------
# Application definition
# -------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # must be high up
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# -------------------------------------------------------------------
# Database (Postgres via .env DATABASE_URL)
# -------------------------------------------------------------------
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
    )
}

# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static files
# -------------------------------------------------------------------
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# Custom user model
# -------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

# -------------------------------------------------------------------
# Email (from .env)
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# -------------------------------------------------------------------
# Redis cache
# -------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# -------------------------------------------------------------------
# Celery
# -------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://redis:6379/0"))
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", TIME_ZONE)

# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True  # dev only
# For production, replace with a safe allowlist:
# CORS_ALLOWED_ORIGINS = [
#     "http://127.0.0.1:5173",
#     "http://localhost:5173",
#     f"http://{os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')[0]}",
# ]
