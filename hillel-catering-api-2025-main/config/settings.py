import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = "Svyat1234"
DEBUG = bool(os.getenv("DJANGO_DEBUG", ""))
ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3-rd party
    "rest_framework",
    "rest_framework_simplejwt",
    # local apps
    "users",
    "food",
    "drf_spectacular"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_DB_NAME", default="catering"),
        "USER": os.getenv("DJANGO_DB_USER", default="postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", default="postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", default="database"),
        "PORT": os.getenv("DJANGO_DB_PORT", default="5432"),
        # "ATOMIC_REQUESTS": True
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "users.User"


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": 'drf_spectacular.openapi.AutoSchema',
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # 'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 1
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Catering API',
    'DESCRIPTION': 'API for Food Orders',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

RATE_LIMITS = {
    'default': {
        'ANON': '100/d',
        'AUTH': '1000/d',
    },
}
# client -> password + login
# server -> access token + refresh token

# client -> token + data
# server -> validate access token, get user by ID, process -> Response

# client -> refresh token
# server -> updated access token + refresh token


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("DJANGO_CACHE_URL", default="redis://cache:6379/0"),
        "TIMEOUT": None, # Посмотрел все сайты где в основном пишут код, с временем жизни, правильно ли я написал?
    }
}

CELERY_BROKER_URL = 'amqp://localhost' 
CELERY_RESULT_BACKEND = 'django-db' 
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_TASK_ROUTES = {
    'hillel-catering.tasks.send_activation_email': {'queue': 'low_priority'},
}

CELERY_TASK_DEFAULT_QUEUE = 'low_priority'
CELERY_TASK_DEFAULT_EXCHANGE = 'tasks'
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'task.low_priority'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", default="mailing")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", default="1025"))
# EMAIL_HOST_USER = "mailpit"
# EMAIL_HOST_PASSWORD = "mailpit"