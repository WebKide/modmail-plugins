# modmail-plugins/RemindMePro/handlers/user_commands.py
from discord.ext import commands
from discord import utils
import discord
import logging

from core.models import Reminder
from core.storage import ReminderStorage
from core.utilities import parse_user_time, validate_future_time
from core.user_settings import UserSettings

log = logging.getLogger(__name__)

class UserCommands(commands.Cog):
    """Handles all user-facing reminder commands"""
    
    def __init__(self, bot, storage: ReminderStorage, user_settings: UserSettings):
        self.bot = bot
        self.storage = storage
        self.user_settings = user_settings
        self.cooldown = commands.CooldownMapping.from_cooldown(3, 60, commands.BucketType.user)

    async def check_dm_status(self, user):
        """Check if user can receive DMs"""
        try:
            await user.send("Testing DM access for RemindMePro plugin", delete_after=1)
            return "✅ Enabled"
        except discord.Forbidden:
            return "❎ Disabled"

    @commands.command(name="remind", aliases=["remindme", "rm"])
    @commands.guild_only()
    async def create_reminder(self, ctx, *, text: str):
        """Create a reminder with time and event"""
        # Rate limiting
        bucket = self.cooldown.get_bucket(ctx.message)
        if bucket.update_rate_limit():
            return await ctx.send("You're using this command too frequently!", delete_after=10)

        dm_status = await self.check_dm_status(ctx.author)
        
        try:
            user_tz = await self.user_settings.get_timezone(ctx.author.id)
            due = parse_user_time(text, user_tz)
            validate_future_time(due)
            
            # Extract reminder text by removing time parts
            reminder_text = self._extract_reminder_text(text)
            
            reminder = Reminder(
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                text=reminder_text,
                due=due,
                timezone=user_tz
            )
            
            reminder_id = await self.storage.create_reminder(reminder)
            
            embed = self._create_reminder_embed(reminder, reminder_id, dm_status)
            await ctx.send(embed=embed, delete_after=260)

        except ValueError as e:
            embed = discord.Embed(
                title="Invalid Format",
                description=str(e),
                color=self.bot.error_color
            )
            embed.add_field(name="📩 Direct Messages", value=dm_status, inline=False)
            await ctx.send(embed=embed, delete_after=260)

    def _extract_reminder_text(self, text: str) -> str:
        """Extract reminder content from command text"""
        # Text extraction logic
        if " to " in text.lower():
            return text.split(" to ", 1)[1].strip()
        return text.strip()

    def _create_reminder_embed(self, reminder: Reminder, reminder_id: str, dm_status: str) -> discord.Embed:
        """Create embed for reminder confirmation"""
        embed = discord.Embed(
            title='✅ Reminder Created',
            description=f'**When:**\n{utils.format_dt(reminder.due, "f")} ({utils.format_dt(reminder.due, "R")})\n'
                       f'**What:**\n```css\n{reminder.text}\n```',
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Reminder ID: {reminder_id}")
        embed.add_field(name="📩 Direct Messages", value=dm_status, inline=False)
        return embed

    @commands.command(name="reminders", aliases=["listreminders", "lr"])
    @commands.guild_only()
    async def list_reminders(self, ctx):
        """List your active reminders"""
        reminders = await self.storage.get_user_reminders(ctx.author.id)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description="You don't have any active reminders yet!",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=260)
            
        # Pagination to be handled here (implementation depends on the UI components)
        
