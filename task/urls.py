from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api

# Create a router for the API
router = DefaultRouter()
router.register(r'tasks', api.TaskViewSet)

app_name = 'task'

urlpatterns = [
    # Web UI URLs
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:task_id>/', views.task_detail, name='detail'),
    path('<int:task_id>/edit/', views.task_edit, name='edit'),
    path('<int:task_id>/toggle/', views.task_toggle_status, name='toggle_status'),
    path('<int:task_id>/delete/', views.task_delete, name='delete'),
    
    # API URLs
    path('api/', include(router.urls)),
]