from django.urls import path
from . import views

urlpatterns = [
    path('', views.bot_list, name='bot_list'),
    path('bot/create/', views.bot_create, name='bot_create'),
    path('bot/<int:bot_id>/', views.bot_detail, name='bot_detail'),
    path('bot/<int:bot_id>/update/', views.bot_update, name='bot_update'),
    path('bot/<int:bot_id>/delete/', views.bot_delete, name='bot_delete'),
    path('bot/<int:bot_id>/toggle/', views.bot_toggle, name='bot_toggle'),
    path('bot/<int:bot_id>/test-message/', views.send_test_message, name='send_test_message'),
] 