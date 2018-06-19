"""Django project settings for ahmia."""
import os
from os.path import dirname, join, abspath

from decouple import config, Csv


# Set the PROJECT_HOME variable.
# This will be used to prepend to all file/directory paths.
PROJECT_HOME = abspath(join(dirname(__file__), '..', '..'))


# Build paths inside the project like this: path("ahmia")
def my_path(*x):
    return join(PROJECT_HOME, *x)


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

# ELASTICSEARCH STUFF
ELASTICSEARCH_TLS_FPRINT = config(
    'ELASTICSEARCH_TLS_FPRINT',
    default="8C:DC:67:EA:C3:B3:97:94:92:30:81:35:8C:C6:D9:2A:E2:E6:8E:3E")
# 'https://ahmia.fi/esconnection/'
ELASTICSEARCH_SERVERS = config('ELASTICSEARCH_SERVERS', default='http://localhost:9200')
# BOTH-INDEX exists in case we want to look into both to onion and i2p addresses ~ currently unused
# ELASTICSEARCH_BOTH_INDEX = config('ELASTICSEARCH_BOTH_INDEX', default='latest-crawl')
ELASTICSEARCH_TOR_INDEX = config('ELASTICSEARCH_TOR_INDEX', default='latest-tor')
ELASTICSEARCH_I2P_INDEX = config('ELASTICSEARCH_I2P_INDEX', default='latest-i2p')
ELASTICSEARCH_TYPE = config('ELASTICSEARCH_TYPE', default='doc')  # todo change/rm when ES 7.x

# Email settings
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default="example@lol.fi")
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default="well_I_am_not_pushing_it_to_git")
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
RECIPIENT_LIST = config('RECIPIENT_LIST', cast=Csv(), default=DEFAULT_FROM_EMAIL)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True


# STATIC
# ------------------------------------------------------------------------------

# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# Absolute path to the directory where collectstatic will collect static files for deployment.
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = my_path('staticfiles/')

# Additional locations the staticfiles app will traverse if the FileSystemFinder finder is enabled
# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATICFILES_DIRS
# STATICFILES_DIRS = [
#     my_path('ahmia/static/'),
#     my_path('search/static/'),
#     my_path('stats/static/')
# ]

# List of finder classes that know how to find static files in various locations.
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


# Make this unique, and don't share it with anybody.
SECRET_KEY = config('SECRET_KEY', default='%*ertqgmh3(t_d=i&ojuc!02wnech_nq#1*s7dbv3h=&ruf7*b')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

)

ROOT_URLCONF = 'ahmia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],

            # loads custom template tags
            'libraries': {
                'ahmia_tags': 'ahmia.template_tags',
            }

        }
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'ahmia',
    'search',
    'stats'
)

# Log everything to the logs directory at the top
LOGFILE_ROOT = my_path('logs')
if not os.path.exists(LOGFILE_ROOT):
    print("Creating logs empty folder %s" % LOGFILE_ROOT)
    os.mkdir(LOGFILE_ROOT)

# Disable automatic default configuration process to apply our own settings
LOGGING_CONFIG = None

# Logging
LOG_LEVEL = config('LOG_LEVEL', default='INFO')   # Debug, Info, Warning, Error, Critical

# Common settings ~ This dict is being updated inside dev.py / prod.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
}
