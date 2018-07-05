import logging.config

from .base import *


DEBUG = config('DEBUG', cast=bool, default=False)

ALLOWED_HOSTS += [
    '.ahmia.fi',   # Allow domain and subdomains
    '.ahmia.fi.',  # Also allow FQDN and subdomains
    '.msydqstlz2kzerdg.onion',
    '.msydqstlz2kzerdg.onion.',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='postgres'),     # Database name
        'USER': config('DB_USER', default='postgres'),     # User with permissions on that DB
        'PASSWORD': config('DB_PASS', default=''),         # Password for the user specified above
        'HOST': config('DB_HOST', default="localhost"),    # Set to empty string for localhost
        'PORT': config('DB_PORT', default=5432, cast=int)  # pbbouncer port
    }
}

DEPLOYMENT_DIR = config('DEPLOYMENT_DIR', default='/usr/local/lib/ahmia-site/ahmia/')

# additionally to default LOGGING settings from base.py
LOGGING.update({
    'handlers': {
        'django_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'django.log'),
            'formatter': 'verbose'
        },
        'ahmia_file': {
            'level': config('LOG_LEVEL', default='INFO'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'ahmia.log'),
            'formatter': 'verbose'
        },
        'search_file': {
            'level': config('LOG_LEVEL', default='INFO'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'search.log'),
            'formatter': 'verbose'
        },
        'stats_file': {
            'level': config('LOG_LEVEL', default='INFO'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'stats.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],  # dont spam email while debugging
            'formatter': 'verbose'
        }
    },
    'loggers': {
        # root is the catch-all logger
        '': {
            'handlers': ['django_file', 'console', 'mail_admins'],
            'level': 'WARNING',
        },
        # our own-defined logger
        'ahmia': {
            'handlers': ['ahmia_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False
        },
        'search': {
            'handlers': ['search_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False
        },
        'stats': {
            'handlers': ['stats_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False
        }
    }
})

logging.config.dictConfig(LOGGING)

