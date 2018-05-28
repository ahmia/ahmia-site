import sys

from .base import *

DEBUG = config('DEBUG', cast=bool, default=True)

DEMO_ENV = ['runserver', 'sqlflush', 'syncdb', 'loaddata', 'shell', 'flush',
            'migrate', 'dumpdata', 'rebuild_index', 'makemigrations']

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',       # Database engine
            'NAME': join(PROJECT_HOME, 'ahmia_db_test')   # Database name
        }
    }
elif [cmd for cmd in DEMO_ENV if cmd in sys.argv]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',  # Database engine
            'NAME': join(PROJECT_HOME, 'ahmia_db')   # Database name
        }
    }
