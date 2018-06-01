import sys

from .base import *

DEBUG = config('DEBUG', cast=bool, default=True)


if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',       # Database engine
            'NAME': join(PROJECT_HOME, 'ahmia_db_test')   # Database name
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',  # Database engine
            'NAME': join(PROJECT_HOME, 'ahmia_db')   # Database name
        }
    }
