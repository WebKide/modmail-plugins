# modmail-plugins/remindmepro/handlers/timezone_commands.py
from discord.ext import commands
import discord
import pytz

from ..corefunc.user_settings import UserSettings
from ..corefunc.utilities import SUPPORTED_LOCATIONS_URL

class TimezoneCommands(commands.Cog):
    """Handles timezone-related commands"""
    
    def __init__(self, bot, user_settings: UserSettings):
        self.bot = bot
        self.user_settings = user_settings

    @commands.group(name="timezone", aliases=["tz"], invoke_without_command=True)
    @commands.guild_only()
    async def timezone(self, ctx):
        """Manage your timezone settings"""
        await ctx.send_help(ctx.command)

    @timezone.command(name="set")
    @commands.guild_only()
    async def set_timezone(self, ctx, timezone: str):
        """Set your timezone (e.g. EST, PST, UTC+3)"""
        try:
            await self.user_settings.set_timezone(ctx.author.id, timezone)
            await ctx.send(f"Your timezone has been set to {timezone}")
        except ValueError as e:
            await ctx.send(f"{str(e)}\nSupported locations: {SUPPORTED_LOCATIONS_URL}")

    @timezone.command(name="view")
    @commands.guild_only()
    async def view_timezone(self, ctx):
        """View your current timezone setting"""
        tz = await self.user_settings.get_timezone(ctx.author.id)
        await ctx.send(f"Your current timezone is set to: {tz}")

    @timezone.command(name="list")
    @commands.guild_only()
    async def list_timezones(self, ctx, search: str = None):
        """List available timezones (optionally filtered by search)"""
        all_tz = pytz.all_timezones
        if search:
            filtered = [tz for tz in all_tz if search.lower() in tz.lower()]
            if not filtered:
                return await ctx.send("No matching timezones found")
            all_tz = filtered[:25]  # Limit to 25 results
        
        description = "\n".join(f"• {tz}" for tz in all_tz[:10])  # Show first 10
        if len(all_tz) > 10:
            description += f"\n...and {len(all_tz)-10} more"
        
        embed = discord.Embed(
            title="Available Timezones",
            description=description,
            color=self.bot.main_color
        )
        await ctx.send(embed=embed)
        
