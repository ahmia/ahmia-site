"""Django WSGI module"""
import os
import sys
from django.core.wsgi import get_wsgi_application

#from django.conf import settings
#sys.path.append(settings.DEPLOYMENT_DIR)
sys.path.append('/usr/local/lib/ahmia-site/ahmia/')

# Path to the settings.py file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahmia.settings.prod")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
application = get_wsgi_application()
