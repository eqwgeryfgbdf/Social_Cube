from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from bot_management.models import Bot, Guild, Command, CommandLog, BotLog
from .utils import (
    send_bot_status_update, 
    send_guild_activity, 
    send_command_log,
    send_dashboard_activity
)


@receiver(post_save, sender=Bot)
def bot_status_changed(sender, instance, created, **kwargs):
    """Send WebSocket update when a bot's status changes"""
    if created:
        # New bot created
        send_dashboard_activity(
            activity_type="bot_created",
            data={
                "bot_id": instance.id,
                "name": instance.name,
                "description": instance.description
            }
        )
    else:
        # Bot updated, check if status changed
        if 'update_fields' in kwargs and kwargs['update_fields'] is not None:
            if 'status' in kwargs['update_fields'] or 'is_active' in kwargs['update_fields']:
                send_bot_status_update(
                    bot_id=instance.id, 
                    status=instance.status,
                    message=f"Bot '{instance.name}' is now {instance.status}"
                )
                
                # Also send to dashboard activity
                send_dashboard_activity(
                    activity_type="bot_status_change",
                    data={
                        "bot_id": instance.id,
                        "name": instance.name,
                        "status": instance.status,
                        "is_active": instance.is_active
                    }
                )


@receiver(post_delete, sender=Bot)
def bot_deleted(sender, instance, **kwargs):
    """Send WebSocket update when a bot is deleted"""
    send_dashboard_activity(
        activity_type="bot_deleted",
        data={
            "bot_id": instance.id,
            "name": instance.name,
        }
    )


@receiver(post_save, sender=Guild)
def guild_status_changed(sender, instance, created, **kwargs):
    """Send WebSocket update when a guild's status changes"""
    if created:
        # New guild added to a bot
        send_guild_activity(
            bot_id=instance.bot.id,
            guild_id=instance.guild_id,
            event_type="guild_added",
            data={
                "guild_id": instance.guild_id,
                "name": instance.name,
                "member_count": instance.member_count,
                "icon": instance.icon
            }
        )
        
        # Also send to dashboard activity
        send_dashboard_activity(
            activity_type="guild_added",
            data={
                "bot_id": instance.bot.id,
                "guild_id": instance.guild_id,
                "name": instance.name
            }
        )
    else:
        # Guild updated
        if 'update_fields' in kwargs and kwargs['update_fields'] is not None:
            if 'is_active' in kwargs['update_fields']:
                status = "active" if instance.is_active else "inactive"
                send_guild_activity(
                    bot_id=instance.bot.id,
                    guild_id=instance.guild_id,
                    event_type="guild_status_change",
                    data={
                        "guild_id": instance.guild_id,
                        "name": instance.name,
                        "status": status
                    }
                )


@receiver(post_delete, sender=Guild)
def guild_removed(sender, instance, **kwargs):
    """Send WebSocket update when a guild is removed from a bot"""
    try:
        send_guild_activity(
            bot_id=instance.bot.id,
            guild_id=instance.guild_id,
            event_type="guild_removed",
            data={
                "guild_id": instance.guild_id,
                "name": instance.name
            }
        )
        
        # Also send to dashboard activity
        send_dashboard_activity(
            activity_type="guild_removed",
            data={
                "bot_id": instance.bot.id,
                "guild_id": instance.guild_id,
                "name": instance.name
            }
        )
    except Exception:
        # Bot might be deleted before the guild
        pass


@receiver(post_save, sender=CommandLog)
def command_executed(sender, instance, created, **kwargs):
    """Send WebSocket update when a command is executed"""
    if created:
        try:
            send_command_log(
                command_id=instance.command.id,
                command_name=instance.command.name,
                bot_id=instance.command.bot.id,
                user_id=instance.user_id,
                status=instance.status,
                guild_id=instance.guild_id if instance.guild_id else None,
                details={
                    "options": instance.options,
                    "error": instance.error if instance.status == 'error' else None
                }
            )
        except Exception:
            # Command or bot might be deleted
            pass


@receiver(post_save, sender=BotLog)
def bot_event_logged(sender, instance, created, **kwargs):
    """Send WebSocket update when an important bot event occurs"""
    if created:
        try:
            # Send to guild activity if guild-specific
            if instance.guild_id:
                send_guild_activity(
                    bot_id=instance.bot.id,
                    guild_id=instance.guild_id,
                    event_type=instance.event_type,
                    data={
                        "description": instance.description,
                        "timestamp": instance.timestamp.isoformat()
                    }
                )
            
            # Important events go to dashboard activity
            if instance.event_type in ['error', 'warning', 'disconnected', 'connected']:
                send_dashboard_activity(
                    activity_type=f"bot_{instance.event_type}",
                    data={
                        "bot_id": instance.bot.id,
                        "name": instance.bot.name,
                        "description": instance.description,
                        "guild_id": instance.guild_id if instance.guild_id else None
                    }
                )
                
                # Also send status update for connection events
                if instance.event_type in ['disconnected', 'connected']:
                    status = "online" if instance.event_type == 'connected' else "offline"
                    send_bot_status_update(
                        bot_id=instance.bot.id,
                        status=status,
                        message=instance.description
                    )
        except Exception:
            # Bot might be deleted
            pass