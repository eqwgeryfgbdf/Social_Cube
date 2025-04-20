from django.db import models

class BotConfig(models.Model):
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=20, blank=True, help_text="Discord channel ID for test messages")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class BotCommand(models.Model):
    bot = models.ForeignKey(BotConfig, on_delete=models.CASCADE, related_name='commands')
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bot.name} - {self.name}" 