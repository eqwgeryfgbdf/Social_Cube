from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import BotConfig, BotCommand
from .forms import BotConfigForm
from .bot import DiscordBot
import logging
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

def bot_list(request):
    bots = BotConfig.objects.all()
    return render(request, 'bot_manager/bot_list.html', {'bots': bots})

def bot_detail(request, bot_id):
    bot = get_object_or_404(BotConfig, id=bot_id)
    commands = bot.commands.all()
    return render(request, 'bot_manager/bot_detail.html', {
        'bot': bot,
        'commands': commands
    })

def bot_create(request):
    if request.method == 'POST':
        form = BotConfigForm(request.POST)
        if form.is_valid():
            bot = form.save()
            messages.success(request, 'Bot configuration created successfully.')
            return redirect('bot_detail', bot_id=bot.id)
    else:
        form = BotConfigForm()
    
    return render(request, 'bot_manager/bot_form.html', {'form': form, 'action': 'Create'})

def bot_update(request, bot_id):
    bot = get_object_or_404(BotConfig, id=bot_id)
    if request.method == 'POST':
        form = BotConfigForm(request.POST, instance=bot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bot configuration updated successfully.')
            return redirect('bot_detail', bot_id=bot.id)
    else:
        form = BotConfigForm(instance=bot)
    
    return render(request, 'bot_manager/bot_form.html', {'form': form, 'action': 'Update'})

def bot_delete(request, bot_id):
    bot = get_object_or_404(BotConfig, id=bot_id)
    if request.method == 'POST':
        try:
            if bot.is_active:
                discord_bot = DiscordBot.get_instance(bot)
                discord_bot.stop()
            bot.delete()
            messages.success(request, 'Bot configuration deleted successfully.')
        except Exception as e:
            logger.error(f"Error deleting bot {bot_id}: {e}", exc_info=True)
            messages.error(request, f'Error deleting bot: {str(e)}')
        return redirect('bot_list')
    
    return render(request, 'bot_manager/bot_confirm_delete.html', {'bot': bot})

def bot_toggle(request, bot_id):
    bot = get_object_or_404(BotConfig, id=bot_id)
    if request.method == 'POST':
        try:
            discord_bot = DiscordBot.get_instance(bot)
            if not bot.is_active:
                logger.info(f"Starting bot {bot_id}...")
                discord_bot.start()
                bot.is_active = True
                messages.success(request, 'Bot started successfully.')
            else:
                logger.info(f"Stopping bot {bot_id}...")
                discord_bot.stop()
                bot.is_active = False
                messages.success(request, 'Bot stopped successfully.')
            bot.save()
        except Exception as e:
            logger.error(f"Error toggling bot {bot_id}: {e}", exc_info=True)
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('bot_detail', bot_id=bot.id)

def send_test_message(request, bot_id):
    bot = get_object_or_404(BotConfig, id=bot_id)
    if request.method == 'POST':
        try:
            if not bot.is_active:
                logger.warning(f"Attempted to send message with inactive bot {bot_id}")
                messages.error(request, "Bot must be running to send test messages")
                return redirect('bot_detail', bot_id=bot.id)
            
            if not bot.channel_id:
                logger.warning(f"Attempted to send message without channel ID for bot {bot_id}")
                messages.error(request, "Channel ID is not configured. Please update the bot configuration.")
                return redirect('bot_detail', bot_id=bot.id)
            
            test_message = request.POST.get('message', '').strip()
            if not test_message:
                test_message = f'Test message from {bot.name}'
            
            logger.info(f"Attempting to send test message for bot {bot_id} to channel {bot.channel_id}")
            discord_bot = DiscordBot.get_instance(bot)
            discord_bot.send_test_message(bot.channel_id, test_message)
            messages.success(request, 'Test message sent successfully.')
            
        except ValueError as e:
            logger.error(f"Configuration error for bot {bot_id}: {str(e)}")
            messages.error(request, f"Configuration error: {str(e)}")
        except RuntimeError as e:
            logger.error(f"Runtime error for bot {bot_id}: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for bot {bot_id}: {str(e)}", exc_info=True)
            messages.error(request, f"Unexpected error: {str(e)}")
    
    return redirect('bot_detail', bot_id=bot.id)

class HomeView(TemplateView):
    template_name = 'home.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ContactView(TemplateView):
    template_name = 'contact.html'

@require_http_methods(["POST"])
@csrf_protect
def contact_form_submit(request):
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Compose email message
        email_message = f"""
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        Message:
        {message}
        """

        # Send email
        send_mail(
            f'Contact Form: {subject}',
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        messages.success(request, 'Your message has been sent successfully!')
        return JsonResponse({'success': True})

    except Exception as e:
        messages.error(request, 'There was an error sending your message. Please try again.')
        return JsonResponse({'success': False, 'error': str(e)}) 