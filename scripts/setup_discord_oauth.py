#!/usr/bin/env python
"""
Script to setup Discord OAuth2 configuration in the database.
This creates a SocialApp record for the Django-allauth integration.
"""

import os
import sys
import django
from django.conf import settings
from django.contrib.sites.models import Site

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
django.setup()

def setup_discord_oauth():
    """Configure Discord OAuth2 in the database."""
    from allauth.socialaccount.models import SocialApp
    
    # Get the site
    site, _ = Site.objects.get_or_create(pk=1)
    site.domain = 'localhost:8000'
    site.name = 'Social Cube'
    site.save()
    
    # Get Discord credentials from environment
    client_id = settings.DISCORD_CLIENT_ID
    client_secret = settings.DISCORD_CLIENT_SECRET
    
    if not client_id or not client_secret:
        print("Error: DISCORD_CLIENT_ID or DISCORD_CLIENT_SECRET environment variables are not set.")
        print("Please set these variables in your .env file and try again.")
        sys.exit(1)
    
    # Create or update the Discord SocialApp
    social_app, created = SocialApp.objects.update_or_create(
        provider='discord',
        defaults={
            'name': 'Discord',
            'client_id': client_id,
            'secret': client_secret,
            'key': '',  # Discord doesn't use this field
        }
    )
    
    # Connect the SocialApp to the site
    social_app.sites.add(site)
    
    if created:
        print(f"Successfully created Discord OAuth2 configuration in the database.")
    else:
        print(f"Successfully updated Discord OAuth2 configuration in the database.")

if __name__ == '__main__':
    setup_discord_oauth()