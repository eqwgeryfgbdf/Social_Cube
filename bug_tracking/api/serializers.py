"""
Serializers for the bug tracking API.

These serializers convert bug tracking models to and from JSON for the API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from bug_tracking.models import Bug, BugComment, BugAttachment, BugTag, BugHistory, BugSubscription
from logging_system.models import ErrorLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in bug-related contexts."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class BugTagSerializer(serializers.ModelSerializer):
    """Serializer for bug tags."""
    
    class Meta:
        model = BugTag
        fields = ['id', 'name', 'color', 'description']


class BugCommentSerializer(serializers.ModelSerializer):
    """Serializer for bug comments."""
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = BugComment
        fields = [
            'id', 'bug', 'author', 'content', 'created_at', 
            'updated_at', 'is_internal'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set the author to the current user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class BugAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for bug attachments."""
    uploader = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BugAttachment
        fields = [
            'id', 'bug', 'uploader', 'file', 'file_url', 'filename',
            'content_type', 'size', 'created_at'
        ]
        read_only_fields = ['id', 'uploader', 'file_url', 'created_at']
    
    def get_file_url(self, obj):
        """Get the URL for the attachment file."""
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def create(self, validated_data):
        # Set the uploader to the current user
        validated_data['uploader'] = self.context['request'].user
        return super().create(validated_data)


class BugHistorySerializer(serializers.ModelSerializer):
    """Serializer for bug history entries."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BugHistory
        fields = [
            'id', 'bug', 'user', 'action', 'timestamp', 
            'changes', 'comment', 'attachment'
        ]
        read_only_fields = ['id', 'user', 'timestamp']


class BugSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for bug subscriptions."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BugSubscription
        fields = [
            'id', 'bug', 'user', 'created_at', 
            'email_notifications', 'in_app_notifications'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        # Set the user to the current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BugListSerializer(serializers.ModelSerializer):
    """Serializer for listing bugs."""
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    tags = BugTagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bug
        fields = [
            'id', 'title', 'status', 'severity', 'reporter', 
            'assignee', 'created_at', 'updated_at', 'tags',
            'comment_count', 'attachment_count'
        ]
    
    def get_comment_count(self, obj):
        """Get the number of comments on the bug."""
        return obj.comments.count()
    
    def get_attachment_count(self, obj):
        """Get the number of attachments on the bug."""
        return obj.attachments.count()


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for ErrorLog model references in bugs."""
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'level', 'logger_name', 'message', 'exception_type',
            'request_path', 'timestamp', 'additional_data'
        ]
        read_only_fields = fields


class BugDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed bug information."""
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    tags = BugTagSerializer(many=True, read_only=True)
    comments = BugCommentSerializer(many=True, read_only=True)
    attachments = BugAttachmentSerializer(many=True, read_only=True)
    history = BugHistorySerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    error_log = ErrorLogSerializer(read_only=True)
    
    class Meta:
        model = Bug
        fields = [
            'id', 'title', 'description', 'status', 'severity',
            'reporter', 'assignee', 'created_at', 'updated_at',
            'resolved_at', 'closed_at', 'environment', 'browser',
            'operating_system', 'stacktrace', 'steps_to_reproduce',
            'expected_behavior', 'actual_behavior', 'tags',
            'comments', 'attachments', 'history', 'is_subscribed',
            'error_log', 'occurrence_count', 'error_hash', 'error_type',
            'error_location', 'error_line'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'resolved_at', 
            'closed_at', 'comments', 'attachments', 'history'
        ]
    
    def get_is_subscribed(self, obj):
        """Check if the current user is subscribed to the bug."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriptions.filter(user=request.user).exists()
        return False


class BugCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bugs."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Bug
        fields = [
            'title', 'description', 'severity', 'status',
            'environment', 'browser', 'operating_system',
            'stacktrace', 'steps_to_reproduce', 'expected_behavior',
            'actual_behavior', 'tag_ids', 'error_log'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set the reporter to the current user
        validated_data['reporter'] = self.context['request'].user
        
        # Create the bug
        bug = super().create(validated_data)
        
        # Add tags
        if tag_ids:
            tags = BugTag.objects.filter(id__in=tag_ids)
            bug.tags.set(tags)
        
        return bug


class BugUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bugs."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    assignee_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = Bug
        fields = [
            'title', 'description', 'severity', 'status',
            'environment', 'browser', 'operating_system',
            'stacktrace', 'steps_to_reproduce', 'expected_behavior',
            'actual_behavior', 'tag_ids', 'assignee_id'
        ]
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        assignee_id = validated_data.pop('assignee_id', None)
        
        # Update the bug
        bug = super().update(instance, validated_data)
        
        # Update tags if provided
        if tag_ids is not None:
            tags = BugTag.objects.filter(id__in=tag_ids)
            bug.tags.set(tags)
        
        # Update assignee if provided
        if assignee_id is not None:
            if assignee_id:
                try:
                    bug.assignee = User.objects.get(id=assignee_id)
                except User.DoesNotExist:
                    pass
            else:
                bug.assignee = None
            bug.save()
        
        return bug