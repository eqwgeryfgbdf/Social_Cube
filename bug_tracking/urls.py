"""
URL configuration for the bug tracking application.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from bug_tracking import views
from bug_tracking.api import views as api_views
from bug_tracking.api.error_reporter import ClientErrorReportView
from bug_tracking import notification_views

# API router setup
router = DefaultRouter()
router.register(r'bugs', api_views.BugViewSet, basename='api-bug')
router.register(r'comments', api_views.BugCommentViewSet, basename='api-comment')
router.register(r'attachments', api_views.BugAttachmentViewSet, basename='api-attachment')
router.register(r'tags', api_views.BugTagViewSet, basename='api-tag')
router.register(r'history', api_views.BugHistoryViewSet, basename='api-history')
router.register(r'subscriptions', api_views.BugSubscriptionViewSet, basename='api-subscription')

app_name = 'bug_tracking'

urlpatterns = [
    # Web UI URLs
    path('', views.bug_list, name='bug_list'),
    path('<uuid:pk>/', views.bug_detail, name='bug_detail'),
    path('<uuid:pk>/update/', views.bug_update, name='bug_update'),
    path('<uuid:pk>/delete/', views.bug_delete, name='bug_delete'),
    path('<uuid:pk>/assign/', views.bug_assign, name='bug_assign'),
    path('<uuid:pk>/change-status/', views.bug_change_status, name='bug_change_status'),
    path('<uuid:pk>/add-comment/', views.add_comment, name='add_comment'),
    path('<uuid:pk>/add-attachment/', views.add_attachment, name='add_attachment'),
    path('<uuid:pk>/subscribe/', views.bug_subscribe, name='bug_subscribe'),
    path('<uuid:pk>/unsubscribe/', views.bug_unsubscribe, name='bug_unsubscribe'),
    path('create/', views.bug_create, name='bug_create'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('dashboard/', views.bug_dashboard, name='bug_dashboard'),
    
    # Notification URLs
    path('notifications/', notification_views.notifications_list, name='notifications'),
    path('notifications/settings/', notification_views.notification_settings, name='notification_settings'),
    path('notifications/mark-read/<uuid:notification_id>/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', notification_views.mark_all_read, name='mark_all_read'),
    path('notifications/count/', notification_views.notification_count, name='notification_count'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/errors/report/', ClientErrorReportView.as_view(), name='api-error-report'),
]