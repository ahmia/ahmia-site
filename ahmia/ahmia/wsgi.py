"""Django WSGI module"""
import os
import sys

from django.core.wsgi import get_wsgi_application

# todo move this to settings/envs
sys.path.append('/usr/local/lib/ahmia-site/ahmia/')

# Path to the settings.py file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahmia.settings")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
application = get_wsgi_application()
