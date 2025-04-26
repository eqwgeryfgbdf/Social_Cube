"""
WSGI config for social_cube project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_cube.settings')

application = get_wsgi_application() 