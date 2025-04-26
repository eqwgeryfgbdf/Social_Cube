"""
URL configuration for social_cube project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Landing page (redirect to dashboard home)
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='index'),
    
    # Main apps
path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
# Only use the dashboard integrated taskmaster to avoid conflicts
# path('tasks/', include(('taskmaster.urls', 'taskmaster'), namespace='taskmaster')),
    
# Bot management app
path('bots/', include(('bot_management.urls', 'bot_management'), namespace='bot_management')),
    
# API endpoints
path('api/', include(('api.urls', 'api'), namespace='api')),
    
    # Authentication
    path('accounts/', include('allauth.urls')),  # Django-allauth URLs
    path('auth/', include([
        path('discord/', include(('dashboard.auth_urls', 'discord_auth'), namespace='discord_auth')),
        path('accounts/', include('django.contrib.auth.urls')),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 