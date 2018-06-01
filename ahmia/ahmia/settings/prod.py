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
