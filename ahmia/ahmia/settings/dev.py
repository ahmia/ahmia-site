import logging.config
from .base import *

DEBUG = config('DEBUG', cast=bool, default=True)

# import sys
# if 'test' in sys.argv:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',       # Database engine
#             'NAME': ROOT_PATH('ahmia_db_test')   # Database name
#         }
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',  # Database engine
#             'NAME': ROOT_PATH('ahmia_db')   # Database name
#         }
#     }
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
            'level': config('LOG_LEVEL', default='INFO'),
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
