import logging.config
import sys

from .base import *

DEBUG = config('DEBUG', cast=bool, default=True)


if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',       # Database engine
            'NAME': my_path('ahmia_db_test')   # Database name
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',  # Database engine
            'NAME': my_path('ahmia_db')   # Database name
        }
    }

# additionally to default LOGGING settings from base.py
LOGGING.update({
    'handlers': {
        'django_file': {
            'level': config('LOG_LEVEL', default='INFO'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'django.log'),
            'formatter': 'verbose'
        },
        'ahmia_file': {
            'level': config('LOG_LEVEL', default='DEBUG'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'ahmia.log'),
            'formatter': 'verbose'
        },
        'search_file': {
            'level': config('LOG_LEVEL', default='DEBUG'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'search.log'),
            'formatter': 'verbose'
        },
        'stats_file': {
            'level': config('LOG_LEVEL', default='DEBUG'),
            'class': 'logging.handlers.WatchedFileHandler',  # log rotation with logrotate
            'filename': join(LOGFILE_ROOT, 'stats.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': config('LOG_LEVEL', default='DEBUG'),
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
            'level': config('LOG_LEVEL', default='INFO'),
        },
        # our own-defined loggers
        'ahmia': {
            'handlers': ['ahmia_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='DEBUG'),
            'propagate': False
        },
        'search': {
            'handlers': ['search_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='DEBUG'),
            'propagate': False
        },
        'stats': {
            'handlers': ['stats_file', 'console', 'mail_admins'],
            'level': config('LOG_LEVEL', default='DEBUG'),
            'propagate': False
        }
    }
})

logging.config.dictConfig(LOGGING)
