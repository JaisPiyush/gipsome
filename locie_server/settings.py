"""
Django settings for locie_server project.

Generated by 'django-admin startproject' using Django 3.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from socket import gethostname
# import getpass
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%^*2esaf@ou%psce0oc%^tqw@)_55_=f#0wr24-q=ktx^!_zi3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]#['ec2-13-126-115-213.ap-south-1.compute.amazonaws.com', '13.126.115.213',]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.gis',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'locie.apps.LocieConfig',
    'fcm_django',
    'corsheaders',
    'django_hosts',
]

PROJECT_APPS = [
    'locie.apps.LocieConfig',
]



#AUTH USER MODEL
AUTH_USER_MODEL = 'locie.Account'



REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES':[
        'rest_framework.authentication.TokenAuthentication',
    ]
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]

ROOT_URLCONF = 'locie_server.urls'
ROOT_HOSTCONF = 'locie_server.hosts'
DEFAULT_HOST = 'locie_server'
SECURE_SSL_REDIRECT = False
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST =[
    "http://localhost:3000",
    "https://locie.herokuapp.com"
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR+"/templates",],
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

WSGI_APPLICATION = 'locie_server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'imango' if gethostname() == 'jarden' else 'gipsomedb',
        'HOST':'localhost',
        'PORT':'5432',
        'USER':'postgres',
        'PASSWORD':'piyush@103'if gethostname() == 'jarden' else 'krispi@103904'
    }
    # 'default': {
    #     'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #     'NAME': 'gipsomedb',
    #     'HOST':'localhost',
    #     'PORT':'5432',
    #     'USER':'postgres',
    #     'PASSWORD':'krispi@103904' 
    # }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
ADMIN_STATIC = ['/home/jarden/gipsomeserver/lib/python3.6/site-packages/django/contrib/admin/static'] if gethostname() != 'jarden' else []

STATICFILES_DIRS = [] + ADMIN_STATIC

CELERY_BROKER_URL = 'redis://:krispi@103904@localhost:6379//' if gethostname() == 'jarden' else 'redis://:d2xy0QBprYp8a9Dgvhz8mYjURb4jbCHq@redis-19040.c1.ap-southeast-1-1.ec2.cloud.redislabs.com:19040//'
CELERY_RESULT_BACKEND = 'db+postgresql://postgres:piyush@103@localhost:5432/imango' if gethostname() == 'jarden' else 'db+postgresql://postgres:krispi@103904@localhost:5432/gipsomedb'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
