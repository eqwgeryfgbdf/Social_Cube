from django.urls import path
from . import views

app_name = 'bot_management'

urlpatterns = [
    # Bot listing and management
    path('', views.index, name='index'),
    path('bot/new/', views.bot_create, name='bot_create'),
    path('bot/<int:bot_id>/', views.bot_detail, name='bot_detail'),
    path('bot/<int:bot_id>/edit/', views.bot_update, name='bot_update'),
    path('bot/<int:bot_id>/delete/', views.bot_delete, name='bot_delete'),
    path('bot/<int:bot_id>/toggle-status/', views.toggle_bot_status, name='toggle_bot_status'),
    path('bot/<int:bot_id>/logs/', views.bot_logs, name='bot_logs'),
]