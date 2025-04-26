"""
URL Configuration for Social Cube project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('bots/', include(('bot_management.urls', 'bot_management'), namespace='bot_management')),
    path('accounts/', include('allauth.urls')),
    path('', RedirectView.as_view(pattern_name='dashboard:index', permanent=False)),
    
    # API URLs
    path('api/v1/', include([
        path('bot-management/', include('bot_management.api_urls')),
        path('auth/token/', obtain_auth_token, name='api_token_auth'),
    ])),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs if available
    try:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    except ImportError:
        pass