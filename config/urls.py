"""
URL Configuration for Social Cube project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('', RedirectView.as_view(pattern_name='dashboard:index', permanent=False)),
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