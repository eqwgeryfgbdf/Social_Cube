"""
Forms for the bug tracking application.

These forms handle bug creation, updates, comments, and other related functionality.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from bug_tracking.models import (
    Bug, BugComment, BugAttachment, BugTag, NotificationPreference
)


class BugForm(forms.ModelForm):
    """Form for creating and updating bugs."""
    
    class Meta:
        model = Bug
        fields = [
            'title', 'description', 'severity', 'steps_to_reproduce',
            'expected_behavior', 'actual_behavior', 'environment',
            'browser', 'operating_system', 'tags',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'steps_to_reproduce': forms.Textarea(attrs={'rows': 3}),
            'expected_behavior': forms.Textarea(attrs={'rows': 3}),
            'actual_behavior': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(),
        }


class BugCommentForm(forms.ModelForm):
    """Form for adding comments to bugs."""
    
    class Meta:
        model = BugComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Add your comment...')}),
        }


class BugAttachmentForm(forms.ModelForm):
    """Form for uploading attachments to bugs."""
    
    class Meta:
        model = BugAttachment
        fields = ['file']


class BugTagForm(forms.ModelForm):
    """Form for creating and editing bug tags."""
    
    class Meta:
        model = BugTag
        fields = ['name', 'color', 'description']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class BugStatusForm(forms.ModelForm):
    """Form for updating bug status."""
    
    class Meta:
        model = Bug
        fields = ['status']


class BugAssignForm(forms.ModelForm):
    """Form for assigning bugs to users."""
    
    class Meta:
        model = Bug
        fields = ['assignee']


class NotificationPreferenceForm(forms.ModelForm):
    """Form for managing notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'web_notify_new_bugs', 'web_notify_status_changes',
            'web_notify_comments', 'web_notify_assignments',
            'web_notify_mentions', 'email_notify_new_bugs',
            'email_notify_status_changes', 'email_notify_comments',
            'email_notify_assignments', 'email_notify_mentions',
            'email_digest_frequency'
        ]
        widgets = {
            'email_digest_frequency': forms.Select(attrs={
                'class': 'settings-select'
            }),
        }