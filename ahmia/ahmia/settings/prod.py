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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('DB_NAME'),      # Database name
        'USER': config('DB_USER'),      # Not used with sqlite3.
        'PASSWORD': config('DB_PASS'),  # Not used with sqlite3.
        'HOST': config('DB_HOST', default="localhost"),    # Set to empty string for localhost
        'PORT': config('DB_PORT', default=5432, cast=int)  # pbbouncer port
    }
}

DEPLOYMENT_DIR = config('DEPLOYMENT_DIR', default='/usr/local/lib/ahmia-site/ahmia/')
