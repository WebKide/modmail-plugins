# modmail-plugins/RemindMePro/handlers/user_commands.py
from discord.ext import commands
from discord import utils
import discord
import logging
from datetime import datetime
import pytz
from typing import Optional

from core.models import Reminder
from core.storage import ReminderStorage
from core.utilities import parse_user_time, validate_future_time
from core.user_settings import UserSettings
from handlers.timezones_config import TIMEZONE_ALIASES

log = logging.getLogger(__name__)

class UserCommands(commands.Cog):
    """Handles all user-facing reminder commands including timezone checks"""
    
    def __init__(self, bot, storage: ReminderStorage, user_settings: UserSettings):
        self.bot = bot
        self.storage = storage
        self.user_settings = user_settings
        self.timezone_aliases = TIMEZONE_ALIASES
        self.cooldown = commands.CooldownMapping.from_cooldown(3, 60, commands.BucketType.user)
        self.supported_locations = "https://gist.github.com/mjrulesamrat/0c1f7de951d3c508fb3a20b4b0b33a98"

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
            
    @commands.group(name="time", aliases=["timezone", "tz"], invoke_without_command=True)
    async def time_group(self, ctx):
        """Check current times in different timezones"""
        await ctx.send_help(ctx.command)

    @time_group.command(name="check")
    async def check_time(self, ctx, *, timezone_input: Optional[str] = None):
        """Check current time in a specific timezone
        
        Supports:
        - Timezone names (America/New_York)
        - Country names (bolivia)
        - Timezone codes (EST)
        - Flag emojis (🇧🇴)
        - Phone codes (+591)
        """
        try:
            # If no timezone specified, show user's current timezone
            if not timezone_input:
                user_tz = await self.user_settings.get_timezone(ctx.author.id)
                timezone_input = user_tz
                source = "your set timezone"
            else:
                # Check if input is an alias
                normalized_input = timezone_input.lower().strip()
                tz_key = next(
                    (k for k in self.TIMEZONE_ALIASES.keys() 
                     if k.lower() == normalized_input or k == timezone_input),
                    None
                )
                
                if tz_key:
                    timezone_input = self.TIMEZONE_ALIASES[tz_key]
                    source = f"alias '{tz_key}'"
                else:
                    source = "direct timezone"
            
            # Validate timezone
            try:
                tz = pytz.timezone(timezone_input)
            except pytz.UnknownTimeZoneError:
                return await ctx.send(
                    f"Unknown timezone. Try:\n"
                    f"- Country/region name (`bolivia`)\n"
                    f"- Timezone code (`EST`)\n"
                    f"- Flag emoji (`🇧🇴`)\n"
                    f"Or see full list: {self.supported_locations}",
                    delete_after=30
                )
            
            # Get current time and format
            now = datetime.now(tz)
            formatted = now.strftime("%A, %B %d %Y\n%I:%M:%S %p %Z")
            
            # Create embed
            embed = discord.Embed(
                title=f"🕒 Current Time ({tz.zone})",
                description=f"```\n{formatted}\n```",
                color=discord.Color.blue()
            )
            
            # Add timezone info
            offset = now.utcoffset()
            if offset:
                hours = offset.total_seconds() / 3600
                embed.set_footer(
                    text=f"UTC {f'+{hours}' if hours >= 0 else hours} • From {source}"
                )
            
            await ctx.send(embed=embed, delete_after=60)

        except Exception as e:
            await ctx.send(f"Error checking time: {str(e)}", delete_after=15)

    @time_group.command(name="list")
    async def list_timezones(self, ctx, search: Optional[str] = None):
        """List available timezones (optionally filtered by search)"""
        all_zones = pytz.all_timezones
        if search:
            filtered = [zone for zone in all_zones if search.lower() in zone.lower()]
            if not filtered:
                return await ctx.send("No matching timezones found", delete_after=15)
            zones = filtered[:25]  # Limit to 25 results
        else:
            zones = pytz.common_timezones[:25]  # Show common ones by default
            
        description = "\n".join(f"• {zone}" for zone in zones)
        if len(zones) == 25:
            description += "\n...and more (try a specific search)"
            
        embed = discord.Embed(
            title="Available Timezones",
            description=description,
            color=self.bot.main_color
        )
        embed.set_footer(text=f"Use '{ctx.prefix}time check [zone]' to view a timezone")
        await ctx.send(embed=embed, delete_after=60)

    @time_group.command(name="set")
    async def set_timezone(self, ctx, timezone_str: str):
        """Set your timezone for reminders"""
        try:
            # Validate timezone
            if timezone_str not in pytz.all_timezones:
                return await ctx.send(
                    f"Invalid timezone. Use formats like `EST`, `PST`, or `Europe/London`\n"
                    f"Full list: {self.supported_locations}",
                    delete_after=30
                )
            
            await self.user_settings.set_timezone(ctx.author.id, timezone_str)
            await ctx.send(f"Your timezone has been set to `{timezone_str}`", delete_after=15)
            
            # Show example of new timezone
            await self.check_time(ctx, timezone_input=timezone_str)
            
        except Exception as e:
            await ctx.send(f"Error setting timezone: {str(e)}", delete_after=15)
