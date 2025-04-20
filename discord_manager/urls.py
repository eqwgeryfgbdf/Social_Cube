"""
URL configuration for discord_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from bot_manager.views import HomeView, AboutView, ContactView, contact_form_submit

# Non-localized URLs
urlpatterns = [
    path('', RedirectView.as_view(url='/bot/', permanent=False)),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Localized URLs
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('api/contact/', contact_form_submit, name='contact_form_submit'),
    path('bot/', include('bot_manager.urls')),
    prefix_default_language=False
)

# Static and media files for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
