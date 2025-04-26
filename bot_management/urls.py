from django.urls import path
from . import views

app_name = 'bot_management'

urlpatterns = [
    # Will be populated with bot management URLs
    path('', views.index, name='index'),
]