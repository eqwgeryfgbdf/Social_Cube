from django.urls import path
from . import views

app_name = 'logging_system'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Request logs
    path('requests/', views.RequestLogListView.as_view(), name='request_log_list'),
    path('requests/<int:pk>/', views.RequestLogDetailView.as_view(), name='request_log_detail'),
    
    # Audit logs
    path('audit/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('audit/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    
    # Error logs
    path('errors/', views.ErrorLogListView.as_view(), name='error_log_list'),
    path('errors/<int:pk>/', views.ErrorLogDetailView.as_view(), name='error_log_detail'),
]