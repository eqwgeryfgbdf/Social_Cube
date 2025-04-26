from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'bots', api.BotViewSet, basename='bot')
router.register(r'logs', api.BotLogViewSet, basename='botlog')

app_name = 'bot_management_api'

urlpatterns = [
    path('', include(router.urls)),
]