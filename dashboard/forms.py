from django import forms
from django.contrib.auth.models import User
from .models import UserSettings

class UserSettingsForm(forms.ModelForm):
    """Form for managing user settings"""
    
    class Meta:
        model = UserSettings
        fields = [
            'enable_dark_mode', 'dashboard_layout',
            'email_notifications', 'discord_notifications',
            'notify_on_bot_status_change', 'notify_on_server_join',
            'notify_on_command_usage', 'notify_on_error'
        ]
        widgets = {
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dashboard_layout': forms.Select(attrs={'class': 'form-select'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'discord_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_bot_status_change': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_server_join': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_command_usage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_error': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Help texts
        self.fields['enable_dark_mode'].help_text = 'Enable dark mode for the dashboard interface'
        self.fields['dashboard_layout'].help_text = 'Choose your preferred dashboard layout style'
        self.fields['email_notifications'].help_text = 'Receive email notifications for important events'
        self.fields['discord_notifications'].help_text = 'Receive Discord DM notifications for important events'
        self.fields['notify_on_bot_status_change'].help_text = 'Get notified when your bot status changes'
        self.fields['notify_on_server_join'].help_text = 'Get notified when your bot joins a new server'
        self.fields['notify_on_command_usage'].help_text = 'Get notified when your commands are used'
        self.fields['notify_on_error'].help_text = 'Get notified when errors occur with your bot'

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make email required for profile updates
        self.fields['email'].required = True