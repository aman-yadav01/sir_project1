"""

Django settings for myproject project.

"""

from pathlib import Path

import os



BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-%r$fwvee$d!l)j(+s8$bwbg5^5ync*@3-p9slyiu&3s8rhr=7y'

DEBUG = True

ALLOWED_HOSTS = ['*']



INSTALLED_APPS = [

    'django.contrib.admin',

    'django.contrib.auth',

    'django.contrib.contenttypes',

    'django.contrib.sessions',

    'django.contrib.messages',

    'django.contrib.staticfiles',

    'attendance_app',

]



MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]



ROOT_URLCONF = 'myproject.urls'



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



WSGI_APPLICATION = 'myproject.wsgi.application'



DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.sqlite3',

        'NAME': BASE_DIR / 'db.sqlite3',

    }

}



# Custom User Model

AUTH_USER_MODEL = 'attendance_app.User'



AUTH_PASSWORD_VALIDATORS = [

    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},

    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},

    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},

    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},

]



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True



STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [BASE_DIR / 'static']



MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



LOGIN_URL = 'home'

LOGIN_REDIRECT_URL = 'home'

LOGOUT_REDIRECT_URL = 'home'



from django.contrib.messages import constants as messages

MESSAGE_TAGS = {

    messages.DEBUG: 'debug',

    messages.INFO: 'info',

    messages.SUCCESS: 'success',

    messages.WARNING: 'warning',

    messages.ERROR: 'danger',

}


# ==================== WEB PUSH NOTIFICATIONS ====================
VAPID_PUBLIC_KEY = 'BN2QTdaaTluu-e5t9z2C39QE3tS5KRdWk7uFGrIk0fKvEcyIbj-rmM5n_V8L9Lj2REpGNv3m59TJ8v264KutG-M'
VAPID_PRIVATE_PEM_B64 = 'LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ3pUUmdxYTAzcVVwdkh4YkQKSy94eW5wVjBxZGVqMVFFK2hwM1JZT2h4SzVDaFJBTkNBQVRka0UzV21rNWJydm51YmZjOWd0L1VCTjdVdVNrWApWcE83aFJxeUpOSHlyeEhNaUc0L3E1ak9aLzFmQy9TNDlrUktSamI5NXVmVXlmTDl1dUNyclJ2agotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg=='
