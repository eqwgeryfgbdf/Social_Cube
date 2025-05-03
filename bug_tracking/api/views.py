"""
API views for the bug tracking application.

These views provide RESTful endpoints for interacting with the bug tracking system.
"""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from bug_tracking.models import (
    Bug, BugComment, BugAttachment, BugTag, 
    BugHistory, BugSubscription
)
from bug_tracking.api.serializers import (
    BugListSerializer, BugDetailSerializer, BugCreateSerializer,
    BugUpdateSerializer, BugCommentSerializer, BugAttachmentSerializer,
    BugTagSerializer, BugHistorySerializer, BugSubscriptionSerializer
)
from utils.error_handling.exceptions import (
    PermissionDeniedError, ResourceNotFoundError
)


class BugViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bugs."""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'severity', 'reporter', 'assignee']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'severity', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get the queryset of bugs the user can access."""
        queryset = Bug.objects.all()
        
        # Filter by tag if provided
        tag_id = self.request.query_params.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # Filter for bugs without assignee
        unassigned = self.request.query_params.get('unassigned')
        if unassigned and unassigned.lower() == 'true':
            queryset = queryset.filter(assignee__isnull=True)
        
        # Filter by time range
        created_after = self.request.query_params.get('created_after')
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        
        created_before = self.request.query_params.get('created_before')
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        # Text search in multiple fields
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(steps_to_reproduce__icontains=search) |
                Q(expected_behavior__icontains=search) |
                Q(actual_behavior__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Get the appropriate serializer based on the action."""
        if self.action == 'list':
            return BugListSerializer
        elif self.action == 'create':
            return BugCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return BugUpdateSerializer
        return BugDetailSerializer
    
    def perform_create(self, serializer):
        """Create a new bug and record it in the history."""
        bug = serializer.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=bug,
            user=self.request.user,
            action=BugHistory.ACTION_CREATE
        )
        
        # Automatically subscribe the reporter
        BugSubscription.objects.create(
            bug=bug,
            user=self.request.user
        )
    
    def perform_update(self, serializer):
        """Update a bug and record changes in the history."""
        # Get the old state of the bug
        old_bug = self.get_object()
        old_status = old_bug.status
        old_assignee = old_bug.assignee
        
        # Update the bug
        bug = serializer.save()
        
        # Record status change in history
        if old_status != bug.status:
            BugHistory.objects.create(
                bug=bug,
                user=self.request.user,
                action=BugHistory.ACTION_STATUS_CHANGE,
                changes={
                    'old_status': old_status,
                    'new_status': bug.status
                }
            )
        
        # Record assignee change in history
        if old_assignee != bug.assignee:
            BugHistory.objects.create(
                bug=bug,
                user=self.request.user,
                action=BugHistory.ACTION_ASSIGN,
                changes={
                    'old_assignee': old_assignee.username if old_assignee else None,
                    'new_assignee': bug.assignee.username if bug.assignee else None
                }
            )
        
        # Record general update in history
        BugHistory.objects.create(
            bug=bug,
            user=self.request.user,
            action=BugHistory.ACTION_UPDATE
        )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign a bug to a user."""
        bug = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            # Assign to the specified user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                bug.assignee = user
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Unassign
            bug.assignee = None
        
        bug.save()
        
        # Record the assignment in history
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            action=BugHistory.ACTION_ASSIGN,
            changes={
                'assignee': bug.assignee.username if bug.assignee else None
            }
        )
        
        return Response(BugDetailSerializer(bug, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change the status of a bug."""
        bug = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Bug.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = bug.status
        bug.status = new_status
        
        # Set timestamps based on status
        if new_status == Bug.STATUS_RESOLVED and not bug.resolved_at:
            bug.resolved_at = timezone.now()
        elif new_status == Bug.STATUS_CLOSED and not bug.closed_at:
            bug.closed_at = timezone.now()
        
        bug.save()
        
        # Record the status change in history
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            action=BugHistory.ACTION_STATUS_CHANGE,
            changes={
                'old_status': old_status,
                'new_status': new_status
            }
        )
        
        return Response(BugDetailSerializer(bug, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """Subscribe to a bug."""
        bug = self.get_object()
        
        # Check if already subscribed
        subscription, created = BugSubscription.objects.get_or_create(
            bug=bug,
            user=request.user
        )
        
        # Update notification preferences if provided
        if 'email_notifications' in request.data:
            subscription.email_notifications = request.data['email_notifications']
        if 'in_app_notifications' in request.data:
            subscription.in_app_notifications = request.data['in_app_notifications']
        
        subscription.save()
        
        return Response(
            BugSubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from a bug."""
        bug = self.get_object()
        
        try:
            subscription = BugSubscription.objects.get(bug=bug, user=request.user)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BugSubscription.DoesNotExist:
            return Response(
                {"error": "Not subscribed to this bug"},
                status=status.HTTP_404_NOT_FOUND
            )


class BugCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bug comments."""
    serializer_class = BugCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get the queryset of comments the user can access."""
        # Filter by bug if provided
        bug_id = self.request.query_params.get('bug')
        if bug_id:
            return BugComment.objects.filter(bug_id=bug_id)
        return BugComment.objects.all()
    
    def perform_create(self, serializer):
        """Create a new comment and record it in the history."""
        comment = serializer.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=comment.bug,
            user=self.request.user,
            action=BugHistory.ACTION_COMMENT,
            comment=comment
        )


class BugAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bug attachments."""
    serializer_class = BugAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get the queryset of attachments the user can access."""
        # Filter by bug if provided
        bug_id = self.request.query_params.get('bug')
        if bug_id:
            return BugAttachment.objects.filter(bug_id=bug_id)
        return BugAttachment.objects.all()
    
    def perform_create(self, serializer):
        """Create a new attachment and record it in the history."""
        attachment = serializer.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=attachment.bug,
            user=self.request.user,
            action=BugHistory.ACTION_ATTACH,
            attachment=attachment
        )


class BugTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bug tags."""
    queryset = BugTag.objects.all()
    serializer_class = BugTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class BugHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing bug history."""
    serializer_class = BugHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get the queryset of history entries the user can access."""
        # Filter by bug if provided
        bug_id = self.request.query_params.get('bug')
        if bug_id:
            return BugHistory.objects.filter(bug_id=bug_id)
        return BugHistory.objects.all()


class BugSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bug subscriptions."""
    serializer_class = BugSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get the queryset of subscriptions for the current user."""
        return BugSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new subscription for the current user."""
        # Check if already subscribed
        bug_id = serializer.validated_data.get('bug').id
        if BugSubscription.objects.filter(bug_id=bug_id, user=self.request.user).exists():
            raise ValidationError("Already subscribed to this bug")
        
        serializer.save(user=self.request.user)