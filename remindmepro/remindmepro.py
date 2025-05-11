# modmail-plugins/remindmepro/remindmepro.py
import logging
from discord.ext import commands

from .corefunc.storage import ReminderStorage
from .corefunc.user_settings import UserSettings
from .handlers import UserCommands, AdminCommands, TimezoneCommands
from .tasks.service_task import ReminderServiceTask
from .exceptions import ReminderError

log = logging.getLogger("Modmail")

class RemindMePro(commands.Cog):
    """RemindMePro plugin by Webkide
    
    A Discord reminder bot with timezone support, customizable reminders, and admin controls.
    Users can set reminders in natural language (e.g., in 2 hours), manage timezones, and view/edit reminders via interactive menus.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self._setup_dependencies()
        
    def _setup_dependencies(self):
        """Initialize and wire up all components"""
        # Database setup
        # self.db = self.bot.plugin_db.get_partition(self)
        # Core services
        self.storage = ReminderStorage(self.bot)
        self.user_settings = UserSettings(self.bot)
        
        # Handlers
        self.user_commands = UserCommands(self.bot, self.storage, self.user_settings)
        self.admin_commands = AdminCommands(self.bot, self.storage)
        self.timezone_commands = TimezoneCommands(self.bot, self.user_settings)
        
        # Background tasks
        self.service_task = ReminderServiceTask(self.bot, self.storage)
        
    async def cog_load(self):
        try:
            await self.user_settings.load_timezones()
            if not self.service_task.reminder_loop.is_running():
                self.service_task.reminder_loop.start()
        except Exception as e:
            print(f"Failed to start reminder loop: {e}")
            raise
        
    async def cog_unload(self):
        if self.service_task.reminder_loop.is_running():
            self.service_task.reminder_loop.cancel()
            try:
                await self.service_task.reminder_loop
            except asyncio.CancelledError:
                pass

        
async def setup(bot):
    try:
        await bot.add_cog(RemindMePro(bot))
        print("[RemindMePro] Commands registered successfully")
    except Exception as e:
        print(f"[RemindMePro] Failed to register commands: {e}")
