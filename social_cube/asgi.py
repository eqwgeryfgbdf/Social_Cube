"""
ASGI config for social_cube project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_cube.settings')
application = get_asgi_application() 