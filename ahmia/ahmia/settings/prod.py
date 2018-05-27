from .base import *

DEBUG = False

ALLOWED_HOSTS += [
    '.ahmia.fi',   # Allow domain and subdomains
    '.ahmia.fi.',  # Also allow FQDN and subdomains
    '.msydqstlz2kzerdg.onion',
    '.msydqstlz2kzerdg.onion.',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'REQUIRED',             # Database name
        'USER': 'REQUIRED',             # Not used with sqlite3.
        'PASSWORD': 'REQUIRED',         # Not used with sqlite3.
        'HOST': '',             # Set to empty string for localhost
        'PORT': '5432',         # pbbouncer port
    }
}
