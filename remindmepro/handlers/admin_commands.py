# modmail-plugins/remindmepro/handlers/admin_commands.py
from discord.ext import commands
import discord
from typing import List, Optional
from datetime import datetime

from ..corefunc.schemas import Reminder
from ..corefunc.storage import ReminderStorage
from ..corefunc.time import UserFriendlyTime
from ..ui.paginator import ReminderPaginator
# from core import checks
from discord import utils
from core.checks import PermissionLevel

class AdminCommands(commands.Cog):
    """Handles admin-only reminder commands"""
    
    def __init__(self, bot, storage: ReminderStorage):
        self.bot = bot
        self.storage = storage
        self.cooldown = commands.CooldownMapping.from_cooldown(2, 30, commands.BucketType.user)

    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def reminders_admin(self, ctx):
        """Admin reminder management"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def admin_all_reminders(self, ctx, limit: Optional[int] = 50):
        """View all active reminders
        Usage: `?ra all [limit=50]`
        """
        # Rate limiting
        bucket = self.cooldown.get_bucket(ctx.message)
        if bucket.update_rate_limit():
            return await ctx.send("Command is on cooldown. Try again later.", delete_after=10)

        if limit < 1 or limit > 100:
            return await ctx.send("Limit must be between 1 and 100.", delete_after=10)

        reminders = await self.storage.get_all_active_reminders(limit=limit)
        
        if not reminders:
            embed = discord.Embed(
                title='No active reminders found',
                description="There are currently no active reminders in the system.",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=30)

        embeds = []
        for reminder in reminders:
            embeds.append(self._create_admin_reminder_embed(reminder))
        
        # Initialize paginator
        paginator = ReminderPaginator(
            bot=self.bot,
            embeds=embeds,
            storage=self.storage,
            is_admin=True
        )
        
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

    @reminders_admin.command(name="due")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def admin_due_reminders(self, ctx, hours: Optional[int] = 24):
        """View reminders due in the next X hours (default: 24)"""
        reminders = await self.storage.get_due_reminders(hours_ahead=hours)
        
        if not reminders:
            embed = discord.Embed(
                title=f'No reminders due in next {hours} hours',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=30)
        
        embeds = []
        for reminder in reminders:
            embeds.append(self._create_admin_reminder_embed(reminder))
        
        paginator = ReminderPaginator(
            bot=self.bot,
            embeds=embeds,
            storage=self.storage,
            is_admin=True
        )
        
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

    @reminders_admin.command(name="user")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def admin_user_reminders(self, ctx, user: discord.User):
        """View all reminders for a specific user"""
        reminders = await self.storage.get_user_reminders(user.id)
        
        if not reminders:
            embed = discord.Embed(
                title=f'No reminders found for {user.display_name}',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=30)
        
        embeds = []
        for reminder in reminders:
            embeds.append(self._create_admin_reminder_embed(reminder))
        
        paginator = ReminderPaginator(
            bot=self.bot,
            embeds=embeds,
            storage=self.storage,
            is_admin=True
        )
        
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

    def _create_admin_reminder_embed(self, reminder: Reminder) -> discord.Embed:
        """Create embed for admin reminder view"""
        user = self.bot.get_user(reminder.user_id)
        username = user.display_name if user else f"Unknown User ({reminder.user_id})"
        avatar = user.display_avatar.url if user and user.avatar else None
        
        truncated_text = (reminder.text[:200] + '...') if len(reminder.text) > 200 else reminder.text
        
        embed = discord.Embed(
            title=f"⏰ Reminder for {username}",
            description=f"**Content:**\n```{truncated_text}\n```",
            color=self.bot.main_color,
            timestamp=reminder.due
        )
        
        if avatar:
            embed.set_thumbnail(url=avatar)
            
        embed.add_field(
            name="Due",
            value=f"{utils.format_dt(reminder.due, 'f')} ({utils.format_dt(reminder.due, 'R')})",
            inline=False
        )
        
        if reminder.channel_id:
            embed.add_field(
                name="Channel",
                value=f"<#{reminder.channel_id}>",
                inline=True
            )
            
        if reminder.recurring:
            embed.add_field(
                name="Recurring",
                value=reminder.recurring.capitalize(),
                inline=True
            )
            
        embed.add_field(
            name="Status",
            value=reminder.status.capitalize(),
            inline=True
        )
        
        if reminder.undelivered:
            embed.add_field(
                name="Warning",
                value="Previous delivery attempt failed",
                inline=False
            )
            
        embed.set_footer(text=f"Reminder ID: {reminder.id} | Created {utils.format_dt(reminder.created_at, 'R')}")
        return embed

    @reminders_admin.command(name="delete")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def admin_delete_reminder(self, ctx, reminder_id: str):
        """Delete a reminder by ID"""
        try:
            success = await self.storage.mark_completed(reminder_id)
            if success:
                await ctx.send(f"✅ Reminder `{reminder_id}` has been deleted.", delete_after=15)
            else:
                await ctx.send(f"⚠️ Could not find reminder with ID `{reminder_id}`", delete_after=15)
        except Exception as e:
            await ctx.send(f"❌ Error deleting reminder: {str(e)}", delete_after=15)

    @reminders_admin.command(name="cleanup")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def admin_cleanup_reminders(self, ctx, days: int = 30):
        """Clean up completed reminders older than X days (default: 30)"""
        if days < 1:
            return await ctx.send("Days must be at least 1.", delete_after=10)
            
        confirm = await ctx.prompt(
            f"This will permanently delete all completed reminders older than {days} days. Continue?",
            timeout=30
        )
        
        if confirm:
            count = await self.storage.cleanup_old_reminders(days)
            await ctx.send(f"🧹 Deleted {count} old reminders.", delete_after=15)
        else:
            await ctx.send("Cleanup cancelled.", delete_after=10)
    
    @reminders_admin.command(name="cleanall")
    async def admin_clean_all(self, ctx):
        """Clean all completed reminders (admin only)"""
        if await ctx.prompt("This will delete ALL completed reminders. Continue?"):
            count = await self.storage.clean_all_completed()
            await ctx.send(f"Deleted {count} completed reminders")
            
