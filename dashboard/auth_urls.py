from django.urls import path
from . import views

urlpatterns = [
    path('oauth2/login/', views.oauth2_login, name='oauth2_login'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('oauth2/logout/', views.logout_view, name='oauth2_logout'),
] 