from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.serializers.json import DjangoJSONEncoder
import json
import re

from .models import Bot, Guild, GuildSettings, Command, CommandOption, BotLog

class BotForm(forms.ModelForm):
    """Form for creating and editing bots"""
    
    class Meta:
        model = Bot
        fields = ['name', 'description', 'token', 'client_id', 'bot_user_id', 'avatar_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bot Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Bot Description'}),
            'token': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bot Token'}),
            'client_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Client ID'}),
            'bot_user_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bot User ID'}),
            'avatar_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Avatar URL (Optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'name': _('A unique name for your bot'),
            'description': _('A brief description of what your bot does'),
            'token': _('Your Discord bot token (keep this secure!)'),
            'client_id': _('Your Discord application client ID'),
            'bot_user_id': _('Your Discord bot user ID'),
            'avatar_url': _('URL to your bot\'s avatar image (optional)'),
            'is_active': _('Whether the bot can be started and used'),
        }

    def clean_token(self):
        """Validate the bot token"""
        token = self.cleaned_data.get('token')
        
        # Token is optional for updates
        if not token and self.instance and self.instance.pk:
            return token
            
        # Check if token looks valid
        if token and not re.match(r'^[A-Za-z0-9._-]+$', token):
            raise ValidationError(_('Invalid token format. Tokens should only contain letters, numbers, and certain symbols (., _, -).'))
            
        return token

    def clean_client_id(self):
        """Validate the client ID"""
        client_id = self.cleaned_data.get('client_id')
        
        # Check if client_id is numeric
        if client_id and not client_id.isdigit():
            raise ValidationError(_('Client ID must be numeric'))
            
        return client_id
        
    def clean_bot_user_id(self):
        """Validate the bot user ID"""
        bot_user_id = self.cleaned_data.get('bot_user_id')
        
        # Check if bot_user_id is numeric
        if bot_user_id and not bot_user_id.isdigit():
            raise ValidationError(_('Bot User ID must be numeric'))
            
        return bot_user_id

class BotLogForm(forms.ModelForm):
    """Form for viewing and filtering bot logs"""
    
    class Meta:
        model = BotLog
        fields = ['event_type', 'description']
        widgets = {
            'event_type': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'readonly': 'readonly'}),
        }

class CommandForm(forms.ModelForm):
    """Form for creating and updating commands"""
    
    # These fields are not directly on the model but help in form processing
    is_global = forms.BooleanField(required=False, initial=True,
                                  widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                                  help_text="If checked, this command will be available in all servers. If unchecked, select a specific server.")
    guild_choice = forms.ModelChoiceField(queryset=Guild.objects.none(), required=False,
                                         widget=forms.Select(attrs={'class': 'form-select'}),
                                         help_text="The specific server where this command will be available. Only applies if 'Global Command' is unchecked.")
    
    class Meta:
        model = Command
        fields = ['bot', 'name', 'description', 'type', 'default_member_permissions', 
                  'is_dm_enabled', 'is_nsfw', 'is_active']
        widgets = {
            'bot': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'pattern': '^[\\w-]{1,32}$', 
                                          'title': 'Command names must be 1-32 characters and contain only alphanumeric characters, underscores, and hyphens.'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'default_member_permissions': forms.TextInput(attrs={'class': 'form-control'}),
            'is_dm_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_nsfw': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'name': 'Command name, lowercase with no spaces (1-32 characters, letters, numbers, hyphens, underscores only)',
            'description': 'Short description of what the command does (max 100 characters)',
            'type': 'Command type: slash command or context menu',
            'default_member_permissions': 'Discord permission flags for who can use this command (leave blank for everyone)',
            'is_dm_enabled': 'Whether this command can be used in DMs',
            'is_nsfw': 'Whether this command is age-restricted',
            'is_active': 'Whether this command is enabled and should be synced',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance, set up is_global and guild_choice fields
        if self.instance and self.instance.pk:
            self.fields['is_global'].initial = self.instance.guild is None
            
            if self.instance.bot:
                self.fields['guild_choice'].queryset = Guild.objects.filter(
                    bot=self.instance.bot, is_available=True
                ).order_by('name')
            
            if self.instance.guild:
                self.fields['guild_choice'].initial = self.instance.guild
        
        # If 'bot' is in the submitted data, fetch guilds for that bot
        bot_id = None
        if 'data' in kwargs and 'bot' in kwargs['data']:
            bot_id = kwargs['data']['bot']
        elif args and len(args) > 0 and 'bot' in args[0]:
            bot_id = args[0]['bot']
        
        if bot_id:
            self.fields['guild_choice'].queryset = Guild.objects.filter(
                bot_id=bot_id, is_available=True
            ).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        is_global = cleaned_data.get('is_global')
        guild_choice = cleaned_data.get('guild_choice')
        command_type = cleaned_data.get('type')
        description = cleaned_data.get('description')
        
        # If not global, require a guild selection
        if not is_global and not guild_choice:
            self.add_error('guild_choice', 'You must select a server for a server-specific command.')
        
        # For USER and MESSAGE types, description is optional
        if command_type in [2, 3] and not description:  # USER or MESSAGE
            cleaned_data['description'] = ''  # Set to empty string if not provided
        elif command_type == 1 and not description:  # CHAT_INPUT requires description
            self.add_error('description', 'Description is required for slash commands.')
        
        return cleaned_data
    
    def save(self, commit=True):
        command = super().save(commit=False)
        is_global = self.cleaned_data.get('is_global')
        guild_choice = self.cleaned_data.get('guild_choice')
        
        # Set the guild based on the is_global flag
        if is_global:
            command.guild = None
        else:
            command.guild = guild_choice
        
        if commit:
            command.save()
        
        return command

class CommandOptionForm(forms.ModelForm):
    """Form for creating and updating command options"""
    
    class Meta:
        model = CommandOption
        fields = ['command', 'parent', 'name', 'description', 'type', 'required', 'position']
        widgets = {
            'command': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'pattern': '^[\\w-]{1,32}$', 
                                          'title': 'Option names must be 1-32 characters and contain only alphanumeric characters, underscores, and hyphens.'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'position': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    # Fields for different option types
    choices_json = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '[{"name": "Option 1", "value": "option1"}, {"name": "Option 2", "value": "option2"}]'}),
        help_text="JSON array of choices for STRING, INTEGER, and NUMBER types. Each choice must have 'name' and 'value'."
    )
    
    min_value = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Minimum value for INTEGER and NUMBER types."
    )
    
    max_value = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Maximum value for INTEGER and NUMBER types."
    )
    
    channel_types = forms.MultipleChoiceField(
        required=False,
        choices=[(0, 'Text'), (2, 'Voice'), (4, 'Category'), (5, 'Announcement'),
                 (10, 'Announcement Thread'), (11, 'Public Thread'), (12, 'Private Thread'),
                 (13, 'Stage Voice'), (15, 'Forum')],
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        help_text="Channel types that are allowed for CHANNEL type options."
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter parent choices based on the command
        if self.instance and self.instance.command:
            self.fields['parent'].queryset = CommandOption.objects.filter(
                command=self.instance.command,
                type__in=[1, 2]  # Only SUB_COMMAND or SUB_COMMAND_GROUP can be parents
            ).exclude(pk=self.instance.pk)  # Exclude self from parent choices
            
            # Set initial values from option_data
            if 'min_value' in self.instance.option_data:
                self.initial['min_value'] = self.instance.option_data['min_value']
            
            if 'max_value' in self.instance.option_data:
                self.initial['max_value'] = self.instance.option_data['max_value']
            
            if 'choices' in self.instance.option_data:
                self.initial['choices_json'] = json.dumps(self.instance.option_data['choices'], indent=2)
            
            if 'channel_types' in self.instance.option_data:
                self.initial['channel_types'] = self.instance.option_data['channel_types']
    
    def clean_choices_json(self):
        """Validate and parse the choices JSON"""
        choices_json = self.cleaned_data.get('choices_json')
        if not choices_json:
            return None
        
        try:
            choices = json.loads(choices_json)
            
            # Validate that choices is a list
            if not isinstance(choices, list):
                raise ValidationError("Choices must be a JSON array.")
            
            # Validate each choice has name and value
            for choice in choices:
                if not isinstance(choice, dict):
                    raise ValidationError("Each choice must be a JSON object.")
                
                if 'name' not in choice or 'value' not in choice:
                    raise ValidationError("Each choice must have 'name' and 'value' properties.")
                
                # Check that name is a string and not too long
                if not isinstance(choice['name'], str) or len(choice['name']) > 100:
                    raise ValidationError("Choice names must be strings with at most 100 characters.")
                
                # Check that value is a valid type (string, number, or boolean)
                if not isinstance(choice['value'], (str, int, float, bool)):
                    raise ValidationError("Choice values must be strings, numbers, or booleans.")
            
            return choices
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format for choices.")
    
    def clean(self):
        cleaned_data = super().clean()
        option_type = cleaned_data.get('type')
        choices = cleaned_data.get('choices_json')
        min_value = cleaned_data.get('min_value')
        max_value = cleaned_data.get('max_value')
        channel_types = cleaned_data.get('channel_types')
        parent = cleaned_data.get('parent')
        
        # Validate based on option type
        if option_type in [3, 4, 10]:  # STRING, INTEGER, NUMBER
            # These types can have choices
            pass
        elif choices:
            self.add_error('choices_json', f"Choices are only valid for STRING, INTEGER, and NUMBER types, not {self.instance.get_type_display()}.")
        
        if option_type in [4, 10]:  # INTEGER, NUMBER
            # These types can have min/max values
            if min_value is not None and max_value is not None and min_value > max_value:
                self.add_error('max_value', "Maximum value must be greater than or equal to minimum value.")
        elif (min_value is not None or max_value is not None):
            self.add_error('min_value', f"Min/max values are only valid for INTEGER and NUMBER types, not {self.instance.get_type_display()}.")
        
        if option_type == 7:  # CHANNEL
            # This type can have channel_types
            pass
        elif channel_types:
            self.add_error('channel_types', f"Channel types are only valid for CHANNEL type, not {self.instance.get_type_display()}.")
        
        # Check parent compatibility
        if parent:
            if parent.type not in [1, 2]:  # SUB_COMMAND, SUB_COMMAND_GROUP
                self.add_error('parent', f"Parent must be a SUB_COMMAND or SUB_COMMAND_GROUP, not {parent.get_type_display()}.")
            
            if parent.type == 1 and option_type in [1, 2]:  # SUB_COMMAND can't have SUB_COMMAND or SUB_COMMAND_GROUP children
                self.add_error('parent', f"SUB_COMMAND cannot have {self.instance.get_type_display()} children.")
        
        return cleaned_data
    
    def save(self, commit=True):
        option = super().save(commit=False)
        
        # Build option_data based on the option type
        option_data = {}
        
        if option.type in [3, 4, 10]:  # STRING, INTEGER, NUMBER
            choices = self.cleaned_data.get('choices_json')
            if choices:
                option_data['choices'] = choices
        
        if option.type in [4, 10]:  # INTEGER, NUMBER
            min_value = self.cleaned_data.get('min_value')
            max_value = self.cleaned_data.get('max_value')
            
            if min_value is not None:
                option_data['min_value'] = min_value
            
            if max_value is not None:
                option_data['max_value'] = max_value
        
        if option.type == 7:  # CHANNEL
            channel_types = self.cleaned_data.get('channel_types')
            if channel_types:
                option_data['channel_types'] = [int(ct) for ct in channel_types]
        
        option.option_data = option_data
        
        if commit:
            option.save()
        
        return option


class GuildSettingsForm(forms.ModelForm):
    """Form for managing guild-specific settings"""
    
    class Meta:
        model = GuildSettings
        fields = ['prefix', 'notification_channel_id', 'welcome_message', 'goodbye_message',
                  'enable_welcome_messages', 'enable_goodbye_messages', 'enable_member_tracking',
                  'enable_moderation', 'admin_role_id', 'moderator_role_id']
        widgets = {
            'prefix': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 10}),
            'notification_channel_id': forms.Select(attrs={'class': 'form-select'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'goodbye_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enable_welcome_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_goodbye_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_member_tracking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_moderation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'admin_role_id': forms.Select(attrs={'class': 'form-select'}),
            'moderator_role_id': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        guild = kwargs.pop('guild', None)
        super().__init__(*args, **kwargs)
        
        if guild:
            # Populate the channel and role dropdowns with choices from the guild
            text_channels = []
            for channel in guild.channels.filter(type=0).order_by('position', 'name'):
                text_channels.append((channel.channel_id, f"#{channel.name}"))
            
            # Add empty option
            text_channels.insert(0, ('', '---------'))
            
            self.fields['notification_channel_id'].widget = forms.Select(
                attrs={'class': 'form-select'},
                choices=text_channels
            )
            
            # For future implementation when roles are added to the model
            # For now, use text inputs for role IDs
            self.fields['admin_role_id'] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Discord Role ID'})
            )
            self.fields['moderator_role_id'] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Discord Role ID'})
            )
            
            # Help texts
            self.fields['prefix'].help_text = 'Command prefix for this server (e.g., !, $, >)'
            self.fields['notification_channel_id'].help_text = 'Channel for bot notifications and alerts'
            self.fields['welcome_message'].help_text = 'Message sent when a new user joins the server. Use {user} to mention the user.'
            self.fields['goodbye_message'].help_text = 'Message sent when a user leaves the server. Use {user} for the username.'
            self.fields['admin_role_id'].help_text = 'Role ID that can use admin-level bot commands'
            self.fields['moderator_role_id'].help_text = 'Role ID that can use moderation commands'