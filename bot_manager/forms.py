from django import forms
from .models import BotConfig, BotCommand

class BotConfigForm(forms.ModelForm):
    class Meta:
        model = BotConfig
        fields = ['name', 'token', 'channel_id']
        widgets = {
            'token': forms.PasswordInput(render_value=True),
            'channel_id': forms.TextInput(attrs={'placeholder': 'Optional: Enter channel ID for test messages'})
        }

class BotCommandForm(forms.ModelForm):
    class Meta:
        model = BotCommand
        fields = ['name', 'description', 'is_enabled'] 