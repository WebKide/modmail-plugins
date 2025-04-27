# modmail-plugins/RemindMePro/remindmepro.py
import logging
from discord.ext import commands

from .core.storage import ReminderStorage
from .core.user_settings import UserSettings
from .handlers import UserCommands, AdminCommands, TimezoneCommands
from .tasks.service_task import ReminderServiceTask
from .exceptions import ReminderError

log = logging.getLogger(__name__)

class RemindMePro(commands.Cog):
    """Main plugin class that ties all components together"""
    
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
        
    # Command groups are registered here but handled by their respective handlers
    @commands.group(name="remind", aliases=["remindme", "rm"], invoke_without_command=True)
    async def remind(self, ctx, *, text: str):
        """Main remind command (delegated to UserCommands)"""
        await self.user_commands.create_reminder(ctx, text=text)
        
    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    async def reminders_admin(self, ctx):
        """Admin commands group (delegated to AdminCommands)"""
        await self.admin_commands.reminders_admin(ctx)
        
    @commands.group(name="timezone", aliases=["tz"], invoke_without_command=True)
    async def timezone(self, ctx):
        """Timezone commands group (delegated to TimezoneCommands)"""
        await self.timezone_commands.timezone(ctx)
        
