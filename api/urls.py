from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Will be populated with API endpoints
    path('', views.api_root, name='api-root'),
]