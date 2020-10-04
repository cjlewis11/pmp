"""
Django settings for etabotsite project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import platform
import datetime
import json
import logging
import subprocess
import urllib
import mimetypes
from etabotapp.email_alert import SendEmailAlert
from helpers import ensure_keys_exist, get_key_value
# from authlib.django.client import OAuth

DJANGO_ROOT = os.path.dirname(os.path.realpath(__file__))



#Import custom_settings.json or throw warning if not provided.

local_host_url = 'http://127.0.0.1:8000'
prod_host_url = 'https://app.etabot.ai'

try:
    with open('custom_settings.json') as f:
        custom_settings = json.load(f)
    logging.debug('loaded custom_settings.json with keys: \
"{}"'.format(custom_settings.keys()))
    if 'local_host_url' in custom_settings:
        local_host_url = custom_settings['local_host_url']

    if 'prod_host_url' in custom_settings:
        prod_host_url = custom_settings['prod_host_url']

except Exception as e:
    logging.warning('cannot load custom_settings.json due to "{}"'.format(
        e))
    logging.info('loading default settings')
    with open('default_settings.json') as f:
        custom_settings = json.load(f)
    logging.info('loaded default settings.')

CUSTOM_SETTINGS = custom_settings
PROD_HOST_URL = prod_host_url

# Determine if we are running on local mode or production mode
# This is based on custom settings config.
# This makes control of prod environment more controlable cross-platform
LOCAL_MODE = custom_settings.get("LOCAL_MODE", False)


# System email settings
# Must be gathered before logging is initiatied to use for email alerts!

SYS_DOMAIN = local_host_url if LOCAL_MODE else prod_host_url
ADMIN_EMAILS = []
if 'SYS_EMAIL_SETTINGS' in custom_settings:
    sys_email_settings = custom_settings.get('SYS_EMAIL_SETTINGS')
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST_USER = SYS_EMAIL = sys_email_settings.get('DJANGO_SYS_EMAIL', '')
    EMAIL_HOST_PASSWORD = SYS_EMAIL_PWD = sys_email_settings.get(
        'DJANGO_SYS_EMAIL_PWD', '')
    EMAIL_HOST = sys_email_settings.get('DJANGO_EMAIL_HOST', '')
    EMAIL_USE_TLS = sys_email_settings.get('DJANGO_EMAIL_USE_TLS', True)
    EMAIL_PORT = sys_email_settings.get('DJANGO_EMAIL_PORT', 587)
    EMAIL_TOKEN_EXPIRATION_PERIOD_MS = 1000 * sys_email_settings.get(
        'EMAIL_TOKEN_EXPIRATION_PERIOD_S', 24 * 60 * 60)
    DEFAULT_FROM_EMAIL = 'no-reply@etabot.ai'
    ADMIN_EMAILS = sys_email_settings.get('ADMIN_EMAILS',[])
else:
    if not LOCAL_MODE:
        raise NameError('cannot load sys_email_settings as its not in custom_settings.json')
    else:
        logging.warning('cannot load sys_email_settings as its not in custom_settings.json')


log_filename_with_path = get_key_value(
    custom_settings, 'LOG_FILENAME_WITH_PATH', default='/usr/src/app/logging/django_log.txt')
print('log_filename_with_path: {}'.format(log_filename_with_path))

## Logging to File and Logging Configuration
# Logger will modify root logger
# Handlers's levels can be changed to meet the needs of the dev
# django_console controls print outs to the console.
# django_file controls print outs to the logging file either locally or on docker.
# mail_admins controls mailing admins through SendEmailAlert class in email_alert.py

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'django_format': {
            'format': 'django %(asctime)s %(name)-12s %(levelname)-8s %(message)s'
            }
    },
    'filters':{
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'django_console': {
            'level':'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'django_format'
        },
        'django_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'django_format',
            'filename': log_filename_with_path,
            'mode': 'a',
            'maxBytes': 10111000,
            'backupCount': 7
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'etabotapp.email_alert.SendEmailAlert',
            'SYS_DOMAIN': SYS_DOMAIN,
            'SYS_EMAIL': SYS_EMAIL,
            'SYS_EMAIL_PWD': SYS_EMAIL_PWD,
            'EMAIL_HOST': EMAIL_HOST,
            'EMAIL_PORT': EMAIL_PORT,
            'ADMINS': ADMIN_EMAILS,
        }
    },
    'loggers': {
        '': {
            'handlers': ['mail_admins', 'django_console', 'django_file'],
            'propagate': True,
        },
    },
}
# Load logger configuration
# Create logger for settings, shows as root in logs.
# Use logger = logging.getLogger(__name__) at top of modules. This provides
# location information on logging. See etabotapp/tests/test_alert.py for
# example.

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

##Set Logger Level
#If we're in production we don't want anything lower than INFO to show.
#Effectively raises all logging handlers to INFO level and above, ignores
#anything lower.

if LOCAL_MODE:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

#Set HOST_URL based on production or development mode
HOST_URL = local_host_url if LOCAL_MODE else prod_host_url
logger.info('HOST_URL="{}"'.format(HOST_URL))



mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)
# mimetypes.add_type("text/css", ".css", True)
# logging.debug('css type guessed: {}'.format(mimetypes.guess_type('test.css')))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

django_keys = {}
try:
    with open('django_keys_prod.json') as f:
        django_keys = json.load(f)
    if (django_keys['DJANGO_SECRET_KEY'] ==
            'k3ku*za@*z$it7@+6+r46pyjv220++5kn((d)w+gozvleu-fhu' or
            django_keys['DJANGO_FIELD_ENCRYPT_KEY'] ==
            'N4h4avmBpgu_QTDr4k5jO9yUfsMIvfNGnQr21aCLbzw='):
        raise NameError('production keys from django_keys_prod.json are default \
keys - not allowed in production for security reasons')
    logger.info('loaded production keys from django_keys_prod.json')
except Exception as e:
    logger.warning('django_keys_prod.json not loaded due to "{}"'.format(e))
    if LOCAL_MODE:
        logger.warning('production keys "django_keys_prod.json" not found, \
loading default keys in local mode (for production please provide \
"django_keys_prod.json"')
        with open('django_keys.json') as f:
            django_keys = json.load(f)
    else:
        raise NameError('production keys "django_keys_prod.json" not found.\
 Cannot proceed in non-local mode')
logger.debug('loaded django_keys: "{}"'.format(django_keys.keys()))

SECRET_KEY = django_keys['DJANGO_SECRET_KEY']

# Keys used to encrypt the password for TMS accounts
FIELD_ENCRYPTION_KEY = str.encode(django_keys['DJANGO_FIELD_ENCRYPT_KEY'])

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if LOCAL_MODE else False
#DEBUG = False

# Update this in production environment to host ip for security reason
ALLOWED_HOSTS = [
    "*", "app.etabot.ai", "localhost", "127.0.0.1", "0.0.0.0", "dev.etabot.ai"]

# Life span for expiring token
EXPIRING_TOKEN_LIFESPAN = datetime.timedelta(seconds=900)


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'etabotapp',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_expiring_authtoken',
    'corsheaders',
    'encrypted_model_fields',
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

if LOCAL_MODE:
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    CORS_ORIGIN_ALLOW_ALL = True
else:
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

# CORS_ORIGIN_WHITELIST = (
#     'google.com',
#     'auth.atlassian.com',
#     'localhost:4200'
# )

# CORS_ALLOW_HEADERS = (
#     'accept',
#     'accept-encoding',
#     'authorization',
#     'content-type',
#     'dnt',
#     'origin',
#     'user-agent',
#     'x-csrftoken',
#     'x-requested-with',
# )

ROOT_URLCONF = 'etabotsite.urls'

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

logger.info('TEMPLATE_DIR = "{}"'.format(TEMPLATE_DIR))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'etabotsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

local_db = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }




if 'db' in custom_settings:
    database_dict = custom_settings['db']
    ensure_keys_exist(database_dict, ['USER', 'PASSWORD'])
else:
    database_dict = local_db
    logging.warning('local db sqlite is no longer supported. please provide postgres database credentials.')

logging.debug('database_dict: {}'.format(database_dict))

DATABASES = {
    'default': database_dict
}

logger.debug('database: Engine={} Name={} Host={}'.format(
    DATABASES['default']['ENGINE'],
    DATABASES['default']['NAME'],
    DATABASES['default'].get('HOST')))

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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


# OAuth
if 'AUTHLIB_OAUTH_CLIENTS' in custom_settings:
    AUTHLIB_OAUTH_CLIENTS = custom_settings.get('AUTHLIB_OAUTH_CLIENTS')
    logger.debug('loaded AUTHLIB_OAUTH_CLIENTS={}'.format(AUTHLIB_OAUTH_CLIENTS))
else:
    if not LOCAL_MODE:
        raise NameError('cannot load AUTHLIB_OAUTH_CLIENTS as its not in custom_settings.json')
    else:
        logger.warning('cannot load AUTHLIB_OAUTH_CLIENTS as its not in custom_settings.json')

TEST_TMS_CREDENTIALS = {}  # Type: Dict[str, str]
if 'TEST_TMS_CREDENTIALS' in custom_settings:
    TEST_TMS_CREDENTIALS = custom_settings.get('TEST_TMS_CREDENTIALS')
else:
    logger.warning('no TEST_TMS_CREDENTIALS in custom_settings - some tests will not run')

TEST_TMS_DATA = {
    'endpoint': TEST_TMS_CREDENTIALS.get("endpoint", "localhost:8888"),
    'username': TEST_TMS_CREDENTIALS.get("username", "testuser@example.com"),
    'password': TEST_TMS_CREDENTIALS.get("password", "testpassword"),
    'type': 'JI',
    'connectivity_status': {}
}
# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

api_url = HOST_URL + '/api/'
logger.info('updating UI with api endpoint: "{}"'.format(api_url))
byteOutput = subprocess.check_output(
    ['python', 'set_api_url.py', 'static/ng2_app', api_url],
    cwd='etabotapp/')
logger.debug(byteOutput)
logger.info(byteOutput.decode('UTF-8'))

STATIC_URL = '/static/'
STATIC_ROOT = '../static'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = True

if LOCAL_MODE:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_DEFAULT_QUEUE = 'etabotqueue'
CELERY_RESULT_BACKEND = 'db+postgresql://{}:{}@{}:5432/{}'.format(
    DATABASES['default']['USER'],
    DATABASES['default']['PASSWORD'],
    DATABASES['default']['HOST'],
    DATABASES['default']['NAME'],
)  # Disabling the results backend

# Configuring the message broker for Celery Task Scheduling
if custom_settings['MESSAGE_BROKER'].lower() == 'aws':
    # AWS Credentials
    AWS_ACCESS_KEY_ID = get_key_value(custom_settings, 'AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = get_key_value(custom_settings, 'AWS_SECRET_ACCESS_KEY')
    CELERY_DEFAULT_QUEUE = get_key_value(custom_settings, 'CELERY_DEFAULT_QUEUE', default='etabotqueue')
    if AWS_ACCESS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None:
        logger.warning(
            'AWS credentials not found. Skipping Celery settings setup.')
    else:
        # Celery Task Scheduling
        BROKER_URL = 'sqs://{0}:{1}@'.format(
            urllib.parse.quote(AWS_ACCESS_KEY_ID, safe=''),
            urllib.parse.quote(AWS_SECRET_ACCESS_KEY, safe='')
        )

        BROKER_TRANSPORT_OPTIONS = {
            'region': custom_settings.get('AWS_SQS_REGION', 'us-west-2'),
            'polling_interval': 20,
        }

elif custom_settings['MESSAGE_BROKER'].lower() == 'rabbitmq':

    # RabbitMQ Credentials
    RMQ_USER = custom_settings['RMQ_USER']
    RMQ_PASS = custom_settings['RMQ_PASS']
    RMQ_HOST = custom_settings['RMQ_HOST']
    RMQ_VHOST = custom_settings['RMQ_VHOST']

    BROKER_URL = 'amqp://{user}:{pw}@{host}:5672/{vhost}'.format(
        user=urllib.parse.quote(RMQ_USER, safe=''),
        pw=urllib.parse.quote(RMQ_PASS, safe=''),
        host=urllib.parse.quote(RMQ_HOST, safe=''),
        vhost=urllib.parse.quote(RMQ_VHOST, safe='')
    )

    logger.debug('celery settings setup complete')
logger.info('BROKER_URL: {}'.format(BROKER_URL))
logger.info('CELERY_DEFAULT_QUEUE: {}'.format(CELERY_DEFAULT_QUEUE))
logger.debug('setting.py is done')
EXPIRING_TOKEN_LIFESPAN = datetime.timedelta(days=1)

logger.error("This is a test of error notification.")
