from django.test import TestCase
from django.contrib.auth.models import User
from bot_management.models import Bot, Guild, Command, CommandOption, CommandLog
from bot_management.tests.test_models import BotBaseTestCase

class CommandModelTest(BotBaseTestCase):
    """Tests for the Command model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test guild
        self.guild = Guild.objects.create(
            bot=self.bot,
            guild_id='123456789',
            name='Test Guild',
            owner_id='987654321',
            member_count=100,
            is_available=True
        )
        
        # Create a test global command
        self.global_command = Command.objects.create(
            bot=self.bot,
            name='test_global',
            description='A test global command',
            type=1,
            is_dm_enabled=True,
            is_active=True
        )
        
        # Create a test guild-specific command
        self.guild_command = Command.objects.create(
            bot=self.bot,
            guild=self.guild,
            name='test_guild',
            description='A test guild command',
            type=1,
            is_dm_enabled=False,
            is_active=True
        )
    
    def test_command_string_representation(self):
        """Test the string representation of a Command"""
        self.assertEqual(str(self.global_command), 'test_global (Global)')
        self.assertEqual(str(self.guild_command), 'test_guild - Test Guild')
    
    def test_command_fields(self):
        """Test that command fields are saved correctly"""
        self.assertEqual(self.global_command.bot, self.bot)
        self.assertIsNone(self.global_command.guild)
        self.assertEqual(self.global_command.name, 'test_global')
        self.assertEqual(self.global_command.description, 'A test global command')
        self.assertEqual(self.global_command.type, 1)
        self.assertTrue(self.global_command.is_dm_enabled)
        self.assertTrue(self.global_command.is_active)
        
        self.assertEqual(self.guild_command.bot, self.bot)
        self.assertEqual(self.guild_command.guild, self.guild)
        self.assertEqual(self.guild_command.name, 'test_guild')
        self.assertEqual(self.guild_command.description, 'A test guild command')
        self.assertEqual(self.guild_command.type, 1)
        self.assertFalse(self.guild_command.is_dm_enabled)
        self.assertTrue(self.guild_command.is_active)
    
    def test_to_discord_json(self):
        """Test the to_discord_json method"""
        global_json = self.global_command.to_discord_json()
        self.assertEqual(global_json['name'], 'test_global')
        self.assertEqual(global_json['description'], 'A test global command')
        self.assertEqual(global_json['type'], 1)
        self.assertTrue(global_json['dm_permission'])
        
        guild_json = self.guild_command.to_discord_json()
        self.assertEqual(guild_json['name'], 'test_guild')
        self.assertEqual(guild_json['description'], 'A test guild command')
        self.assertEqual(guild_json['type'], 1)
        self.assertFalse(guild_json['dm_permission'])

class CommandOptionTest(BotBaseTestCase):
    """Tests for the CommandOption model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test command
        self.command = Command.objects.create(
            bot=self.bot,
            name='test_command',
            description='A test command',
            type=1,
            is_active=True
        )
        
        # Create a test string option
        self.string_option = CommandOption.objects.create(
            command=self.command,
            name='string_option',
            description='A string option',
            type=3,  # STRING
            required=True,
            position=0
        )
        
        # Create a test integer option with min/max values
        self.integer_option = CommandOption.objects.create(
            command=self.command,
            name='integer_option',
            description='An integer option',
            type=4,  # INTEGER
            required=False,
            position=1,
            option_data={
                'min_value': 1,
                'max_value': 100
            }
        )
        
        # Create a test subcommand group
        self.subcommand_group = CommandOption.objects.create(
            command=self.command,
            name='subcommand_group',
            description='A subcommand group',
            type=2,  # SUB_COMMAND_GROUP
            required=False,
            position=2
        )
        
        # Create a test subcommand within the group
        self.subcommand = CommandOption.objects.create(
            command=self.command,
            parent=self.subcommand_group,
            name='subcommand',
            description='A subcommand',
            type=1,  # SUB_COMMAND
            required=False,
            position=0
        )
    
    def test_option_string_representation(self):
        """Test the string representation of a CommandOption"""
        self.assertEqual(str(self.string_option), 'string_option (STRING)')
        self.assertEqual(str(self.integer_option), 'integer_option (INTEGER)')
        self.assertEqual(str(self.subcommand_group), 'subcommand_group (SUB_COMMAND_GROUP)')
        self.assertEqual(str(self.subcommand), 'subcommand (SUB_COMMAND)')
    
    def test_option_fields(self):
        """Test that option fields are saved correctly"""
        self.assertEqual(self.string_option.command, self.command)
        self.assertIsNone(self.string_option.parent)
        self.assertEqual(self.string_option.name, 'string_option')
        self.assertEqual(self.string_option.description, 'A string option')
        self.assertEqual(self.string_option.type, 3)
        self.assertTrue(self.string_option.required)
        
        self.assertEqual(self.integer_option.command, self.command)
        self.assertIsNone(self.integer_option.parent)
        self.assertEqual(self.integer_option.name, 'integer_option')
        self.assertEqual(self.integer_option.description, 'An integer option')
        self.assertEqual(self.integer_option.type, 4)
        self.assertFalse(self.integer_option.required)
        self.assertEqual(self.integer_option.option_data['min_value'], 1)
        self.assertEqual(self.integer_option.option_data['max_value'], 100)
        
        self.assertEqual(self.subcommand.command, self.command)
        self.assertEqual(self.subcommand.parent, self.subcommand_group)
        self.assertEqual(self.subcommand.name, 'subcommand')
        self.assertEqual(self.subcommand.description, 'A subcommand')
        self.assertEqual(self.subcommand.type, 1)
        self.assertFalse(self.subcommand.required)
    
    def test_to_discord_json(self):
        """Test the to_discord_json method"""
        string_json = self.string_option.to_discord_json()
        self.assertEqual(string_json['name'], 'string_option')
        self.assertEqual(string_json['description'], 'A string option')
        self.assertEqual(string_json['type'], 3)
        self.assertTrue(string_json['required'])
        
        integer_json = self.integer_option.to_discord_json()
        self.assertEqual(integer_json['name'], 'integer_option')
        self.assertEqual(integer_json['description'], 'An integer option')
        self.assertEqual(integer_json['type'], 4)
        self.assertFalse(integer_json['required'])
        self.assertEqual(integer_json['min_value'], 1)
        self.assertEqual(integer_json['max_value'], 100)

class CommandLogTest(BotBaseTestCase):
    """Tests for the CommandLog model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test command
        self.command = Command.objects.create(
            bot=self.bot,
            name='test_command',
            description='A test command',
            type=1,
            is_active=True
        )
        
        # Create a test command log
        self.log = CommandLog.objects.create(
            command=self.command,
            event_type='COMMAND_CREATED',
            description='Command created for testing',
            details={'user_id': str(self.user.id)}
        )
    
    def test_log_string_representation(self):
        """Test the string representation of a CommandLog"""
        expected = f"test_command - COMMAND_CREATED - {self.log.timestamp}"
        self.assertEqual(str(self.log), expected)
    
    def test_log_fields(self):
        """Test that log fields are saved correctly"""
        self.assertEqual(self.log.command, self.command)
        self.assertEqual(self.log.event_type, 'COMMAND_CREATED')
        self.assertEqual(self.log.description, 'Command created for testing')
        self.assertEqual(self.log.details['user_id'], str(self.user.id))
        self.assertIsNotNone(self.log.timestamp)