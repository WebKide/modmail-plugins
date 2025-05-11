# modmail-plugins/remindmepro/config.py
from datetime import timedelta

class ReminderConfig:
    # Core settings
    DEFAULT_TIMEZONE = "UTC"
    MAX_REMINDER_LENGTH = 400
    MAX_USER_REMINDERS = 30
    REMINDER_CLEANUP_DAYS = 30
    
    # Task settings
    PROCESSING_INTERVAL = 120.0  # seconds
    BATCH_SIZE = 100
    
    # UI settings
    PAGINATOR_TIMEOUT = 120  # seconds
    VIEW_TIMEOUT = 180  # seconds
    REMINDER_ID_PREFIX_LENGTH = 13
    
    # Rate limits
    USER_COOLDOWN_RATE = 3  # commands
    USER_COOLDOWN_PERIOD = 60  # seconds
    
    # Fallback channels (in order of preference)
    FALLBACK_CHANNELS = ["bot-spam", "bot-commands", "general", "off-topic", "bot"]
    
    @classmethod
    def cooldown(cls):
        """Returns a cooldown mapping for commands"""
        from discord.ext import commands
        return commands.CooldownMapping.from_cooldown(
            cls.USER_COOLDOWN_RATE,
            cls.USER_COOLDOWN_PERIOD,
            commands.BucketType.user
        )
