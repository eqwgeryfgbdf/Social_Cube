from django import forms
from .models import Bot, BotLog
import re

class BotForm(forms.ModelForm):
    """Form for creating and editing bots"""
    
    token = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Enter your Discord bot token from the Developer Portal'
    )
    
    class Meta:
        model = Bot
        fields = ['name', 'description', 'token', 'client_id', 'bot_user_id', 'avatar_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'client_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bot_user_id': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_token(self):
        """Validate the bot token format"""
        token = self.cleaned_data.get('token')
        
        # Basic format validation for Discord bot tokens
        if not re.match(r'^[A-Za-z0-9._-]+$', token):
            raise forms.ValidationError("Bot token contains invalid characters")
            
        # Most Discord bot tokens are at least 50 characters long
        if len(token) < 50:
            raise forms.ValidationError("Bot token is too short to be valid")
            
        return token
        
    def clean_client_id(self):
        """Validate the client ID (should be numeric)"""
        client_id = self.cleaned_data.get('client_id')
        
        if not client_id.isdigit():
            raise forms.ValidationError("Client ID must contain only digits")
            
        return client_id
        
    def clean_bot_user_id(self):
        """Validate the bot user ID (should be numeric)"""
        bot_user_id = self.cleaned_data.get('bot_user_id')
        
        if not bot_user_id.isdigit():
            raise forms.ValidationError("Bot user ID must contain only digits")
            
        return bot_user_id

class BotLogForm(forms.ModelForm):
    """Form for creating log entries"""
    
    class Meta:
        model = BotLog
        fields = ['bot', 'event_type', 'description']
        widgets = {
            'bot': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }