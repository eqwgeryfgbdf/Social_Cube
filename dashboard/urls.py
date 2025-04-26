from django.urls import path, include
from . import views

app_name = 'dashboard'

# Bot management URLs
bot_patterns = [
    path('', views.bot_list, name='list'),
    path('add/', views.bot_add, name='add'),
    path('<int:bot_id>/', views.bot_detail, name='detail'),
    path('<int:bot_id>/toggle/', views.bot_toggle, name='toggle'),
]

# Analytics URLs
analytics_patterns = [
    path('', views.stats, name='overview'),
]

urlpatterns = [
    # Main views
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('servers/', views.server_list, name='servers'),
    path('stats/', views.stats, name='stats'),
    
    # OAuth2 endpoints
    path('oauth2/login/', views.oauth2_login, name='oauth2_login'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('logout/', views.logout_view, name='logout'),
    path('oauth2/debug/', views.oauth2_debug, name='oauth2_debug'),
    
    # Bot management
    path('bots/', include((bot_patterns, 'dashboard'), namespace='bot')),
    
    # Analytics
    path('analytics/', include((analytics_patterns, 'dashboard'), namespace='analytics')),
    
    # Taskmaster - use the correct namespace format to avoid conflicts
path('taskmaster/', include('dashboard.taskmaster.urls', namespace='taskmaster')),
]