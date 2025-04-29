# modmail-plugins/remindmepro/remindmepro.py
import logging
from discord.ext import commands

from .corefunc.storage import ReminderStorage
from .corefunc.user_settings import UserSettings
from .handlers import UserCommands, AdminCommands, TimezoneCommands
from .tasks.service_task import ReminderServiceTask
from .exceptions import ReminderError

log = logging.getLogger(__name__)

class RemindMePro(commands.Cog):
    """RemindMePro plugin by Webkide
    
    A Discord reminder bot with timezone support, customizable reminders, and admin controls.
    Users can set reminders in natural language (e.g., "in 2 hours"), manage timezones, and view/edit reminders via interactive menus.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self._setup_dependencies()
        
    def _setup_dependencies(self):
        """Initialize and wire up all components"""
        # Database setup
        self.db = self.bot.plugin_db.get_partition(self)
        
        # Core services
        self.storage = ReminderStorage(self.db)
        self.user_settings = UserSettings(self.db)
        
        # Handlers
        self.user_commands = UserCommands(self.bot, self.storage, self.user_settings)
        self.admin_commands = AdminCommands(self.bot, self.storage)
        self.timezone_commands = TimezoneCommands(self.bot, self.user_settings)
        
        # Background tasks
        self.service_task = ReminderServiceTask(self.bot, self.storage)
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        await self.storage.setup_indexes()
        await self.user_settings.load_timezones()
        log.info("RemindMePro plugin loaded")
        
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        self.service_task.reminder_loop.cancel()
        log.info("RemindMePro plugin unloaded")

        
async def setup(bot):
    await bot.add_cog(RemindMePro(bot))
    
