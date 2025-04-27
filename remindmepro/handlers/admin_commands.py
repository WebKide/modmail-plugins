# modmail-plugins/RemindMePro/handlers/admin_commands.py
from discord.ext import commands
import discord
from typing import List

from core.models import Reminder
from core.storage import ReminderStorage
from core import checks

class AdminCommands(commands.Cog):
    """Handles admin-only reminder commands"""
    
    def __init__(self, bot, storage: ReminderStorage):
        self.bot = bot
        self.storage = storage

    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def reminders_admin(self, ctx):
        """Admin reminder management"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def admin_all_reminders(self, ctx):
        """View all active reminders"""
        reminders = await self.storage.get_due_reminders()  # Would need to add this method
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=260)
        
        # Format reminders for admin view
        embeds = []
        for reminder in reminders:
            embed = self._create_admin_reminder_embed(reminder)
            embeds.append(embed)
        
        # Pagination would be handled here... later

    def _create_admin_reminder_embed(self, reminder: Reminder) -> discord.Embed:
        """Create embed for admin reminder view"""
        user = self.bot.get_user(reminder.user_id)
        username = user.name if user else f"Unknown User ({reminder.user_id})"
        
        embed = discord.Embed(
            title=f"⏰ Reminder for {username}",
            description=f"**Content:**\n```css\n{reminder.text}\n```",
            color=self.bot.main_color
        )
        embed.add_field(
            name="Due",
            value=f"{utils.format_dt(reminder.due, 'f')} ({utils.format_dt(reminder.due, 'R')})",
            inline=False
        )
        if reminder.channel_id:
            embed.add_field(name="Channel", value=f"<#{reminder.channel_id}>", inline=False)
        if reminder.recurring:
            embed.add_field(name="Recurring", value=reminder.recurring.capitalize(), inline=False)
        embed.set_footer(text=f"Reminder ID: {reminder.id}")
        return embed
        
