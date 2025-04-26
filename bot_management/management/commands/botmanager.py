from django.core.management.base import BaseCommand, CommandError
import time
import sys
import signal
import threading
import logging
import asyncio
from bot_management.models import Bot
from bot_management.discord_bot.service import bot_manager

# Configure logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage Discord bots'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['start', 'stop', 'restart', 'status', 'start-all', 'stop-all', 'monitor'],
            required=True,
            help='The action to perform'
        )
        parser.add_argument(
            '--bot-id',
            type=int,
            help='The ID of the bot to manage'
        )
        parser.add_argument(
            '--monitor-time',
            type=int,
            default=0,
            help='How long to run the monitor mode (in seconds, 0 for indefinite)'
        )
        
    def handle(self, *args, **options):
        action = options['action']
        bot_id = options.get('bot_id')
        monitor_time = options.get('monitor_time', 0)
        
        # Start the bot manager
        bot_manager.start()
        
        try:
            if action == 'start':
                self._handle_start(bot_id)
            elif action == 'stop':
                self._handle_stop(bot_id)
            elif action == 'restart':
                self._handle_restart(bot_id)
            elif action == 'status':
                self._handle_status(bot_id)
            elif action == 'start-all':
                self._handle_start_all()
            elif action == 'stop-all':
                self._handle_stop_all()
            elif action == 'monitor':
                self._handle_monitor(monitor_time)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Interrupted by user'))
        finally:
            # Only stop the manager if not in monitor mode
            if action != 'monitor':
                bot_manager.stop()
                
    def _handle_start(self, bot_id):
        if not bot_id:
            raise CommandError('Bot ID is required for the start action')
            
        self.stdout.write(f'Starting bot with ID {bot_id}...')
        
        try:
            # Check if bot exists
            bot = Bot.objects.get(id=bot_id)
            
            # Ensure bot is active
            if not bot.is_active:
                self.stdout.write(self.style.WARNING(f'Bot {bot_id} is marked as inactive'))
                confirm = input('Do you want to start it anyway? (y/n): ')
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.ERROR('Operation cancelled'))
                    return
                    
            # Start the bot
            success = bot_manager.start_bot(bot_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'Bot {bot_id} ({bot.name}) started successfully'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to start bot {bot_id}'))
                
        except Bot.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Bot with ID {bot_id} does not exist'))
            
    def _handle_stop(self, bot_id):
        if not bot_id:
            raise CommandError('Bot ID is required for the stop action')
            
        self.stdout.write(f'Stopping bot with ID {bot_id}...')
        
        # Stop the bot
        success = bot_manager.stop_bot(bot_id)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Bot {bot_id} stopped successfully'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to stop bot {bot_id}'))
            
    def _handle_restart(self, bot_id):
        if not bot_id:
            raise CommandError('Bot ID is required for the restart action')
            
        self.stdout.write(f'Restarting bot with ID {bot_id}...')
        
        # Restart the bot
        success = bot_manager.restart_bot(bot_id)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Bot {bot_id} restarted successfully'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to restart bot {bot_id}'))
            
    def _handle_status(self, bot_id=None):
        if bot_id:
            # Get status for a specific bot
            status = bot_manager.get_bot_status(bot_id)
            
            try:
                bot = Bot.objects.get(id=bot_id)
                self.stdout.write(f'Status for bot {bot_id} ({bot.name}):')
            except Bot.DoesNotExist:
                self.stdout.write(f'Status for bot {bot_id}:')
                
            self._print_bot_status(bot_id, status)
        else:
            # Get status for all bots
            statuses = bot_manager.get_all_bots_status()
            
            if not statuses:
                self.stdout.write('No bots are currently running')
                return
                
            self.stdout.write(f'Status for {len(statuses)} running bots:')
            
            for bot_id, status in statuses.items():
                try:
                    bot = Bot.objects.get(id=bot_id)
                    self.stdout.write(f'\nBot {bot_id} ({bot.name}):')
                except Bot.DoesNotExist:
                    self.stdout.write(f'\nBot {bot_id}:')
                    
                self._print_bot_status(bot_id, status)
                
    def _print_bot_status(self, bot_id, status):
        # Format and print status information
        self.stdout.write(f'  Running: {status["running"]}')
        
        if status["running"]:
            self.stdout.write(f'  Connected: {status["connected"]}')
            self.stdout.write(f'  Healthy: {status["healthy"]}')
            
            if status["connected"]:
                self.stdout.write(f'  Guilds: {status["guilds"]}')
                self.stdout.write(f'  Users: {status["users"]}')
                
                # Format uptime
                uptime = status["uptime"]
                days, remainder = divmod(uptime, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
                self.stdout.write(f'  Uptime: {uptime_str}')
                
                self.stdout.write(f'  Commands used: {status["commands_used"]}')
                
    def _handle_start_all(self):
        self.stdout.write('Starting all active bots...')
        
        # Get all active bots
        active_bots = Bot.objects.filter(is_active=True)
        
        if not active_bots:
            self.stdout.write(self.style.WARNING('No active bots found'))
            return
            
        self.stdout.write(f'Found {len(active_bots)} active bots')
        
        # Start each bot
        success_count = 0
        for bot in active_bots:
            self.stdout.write(f'Starting bot {bot.id} ({bot.name})...')
            
            if bot_manager.start_bot(bot.id):
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR(f'Failed to start bot {bot.id}'))
                
        self.stdout.write(self.style.SUCCESS(f'Successfully started {success_count} of {len(active_bots)} bots'))
        
    def _handle_stop_all(self):
        self.stdout.write('Stopping all running bots...')
        
        # Get all running bots
        running_bots = list(bot_manager.running_bots.keys())
        
        if not running_bots:
            self.stdout.write(self.style.WARNING('No running bots found'))
            return
            
        self.stdout.write(f'Found {len(running_bots)} running bots')
        
        # Stop each bot
        success_count = 0
        for bot_id in running_bots:
            self.stdout.write(f'Stopping bot {bot_id}...')
            
            if bot_manager.stop_bot(bot_id):
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR(f'Failed to stop bot {bot_id}'))
                
        self.stdout.write(self.style.SUCCESS(f'Successfully stopped {success_count} of {len(running_bots)} bots'))
        
    def _handle_monitor(self, monitor_time):
        self.stdout.write('Starting bot monitor mode...')
        
        # Register signal handlers for graceful shutdown
        def handle_signal(sig, frame):
            self.stdout.write(self.style.WARNING('\nShutting down bot manager...'))
            bot_manager.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Start all active bots
        self._handle_start_all()
        
        # Monitor loop
        start_time = time.time()
        try:
            while True:
                # Check if we've reached the time limit
                if monitor_time > 0 and time.time() - start_time >= monitor_time:
                    self.stdout.write(self.style.SUCCESS(f'Monitor completed after {monitor_time} seconds'))
                    break
                    
                # Print status periodically
                self.stdout.write('\n--- Bot Status Update ---')
                self._handle_status()
                
                # Wait before next status update
                time.sleep(60)
        finally:
            # Always stop the manager when exiting
            bot_manager.stop()