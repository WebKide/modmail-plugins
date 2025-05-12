# modmail-plugins/remindmepro/tasks/service_task.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import discord
from discord.ext import tasks
from discord.ui import View

from ..corefunc.schemas import Reminder
from ..corefunc.storage import ReminderStorage
from ..ui.views import ReminderControlsView

log = logging.getLogger(__name__)

class ReminderServiceTask:
    """Background service for processing reminders"""
    
    def __init__(self, bot, storage: ReminderStorage):
        self.bot = bot
        self.storage = storage
        self._current_batch: List[Reminder] = []
        self._processing_lock = asyncio.Lock()
        # self.reminder_loop.start()

    @tasks.loop(seconds=120.0)
    async def reminder_loop(self):
        """Main processing loop for reminders"""
        async with self._processing_lock:
            await self.process_due_reminders()

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        """Wait until bot is ready"""
        await self.bot.wait_until_ready()
        log.info("Reminder service started")

    @reminder_loop.after_loop
    async def after_reminder_loop(self):
        """Cleanup when loop stops"""
        log.info("Reminder service stopped")

    async def process_due_reminders(self, batch_size: int = 100):
        """Process a batch of due reminders"""
        try:
            self._current_batch = await self.storage.get_due_reminders(batch_size)
            log.debug(f"Processing {len(self._current_batch)} due reminders")
            
            for reminder in self._current_batch:
                await self.process_single_reminder(reminder)
                
        except Exception as e:
            log.error(f"Error processing reminders batch:\n{str(e)}", exc_info=True)

    async def process_single_reminder(self, reminder: Reminder):
        """Handle delivery and state update for a single reminder"""
        try:
            # Handle recurring reminders first
            if reminder.recurring:
                await self.handle_recurring_reminder(reminder)
                return
                
            # Try to deliver the reminder
            delivered = await self.deliver_reminder(reminder)
            
            if delivered:
                await self.storage.mark_completed(str(reminder.id))
            else:
                await self.storage.update_reminder(
                    str(reminder.id),
                    {"undelivered": True}
                )
                
        except Exception as e:
            log.error(f"Failed to process reminder {reminder.id}:\n{str(e)}", exc_info=True)

    async def handle_recurring_reminder(self, reminder: Reminder):
        """Process recurring reminders and schedule next occurrence"""
        try:
            # First deliver the current reminder
            await self.deliver_reminder(reminder)
            
            # Calculate and schedule next occurrence
            user_tz = ZoneInfo(reminder.timezone)
            local_due = reminder.due.astimezone(user_tz)
            next_due = self.calculate_next_occurrence(local_due, reminder.recurring)
            next_due_utc = user_tz.localize(next_due).astimezone(pytz.UTC)
            await self.storage.update_reminder(
                str(reminder.id),
                {"due": next_due}
            )
            
        except Exception as e:
            log.error(f"Failed to process recurring reminder {reminder.id}: {str(e)}")

    async def deliver_reminder(self, reminder: Reminder) -> bool:
        """Attempt to deliver reminder to user with channel fallback logic"""
        try:
            user = await self.bot.get_or_fetch_user(reminder.user_id)
            if not user:
                log.warning(f"User {reminder.user_id} not found for reminder {reminder.id}")
                return False
                
            embed = self.create_reminder_embed(reminder)
            view = ReminderControlsView(self.storage, reminder)
            
            # Try delivery methods in order
            delivered = await self._try_original_channel(reminder, embed, view)
            if not delivered:
                delivered = await self._try_fallback_channels(user.guild, user, embed, view)
            if not delivered:
                delivered = await self._try_dm(user, embed, view)
                
            return delivered
            
        except Exception as e:
            log.error(f"Failed to deliver reminder {reminder.id}: {str(e)}")
            return False

    async def _try_original_channel(self, reminder: Reminder, embed: discord.Embed, view: View) -> bool:
        """Try sending to the original channel where reminder was created"""
        if not reminder.channel_id:
            return False
            
        try:
            channel = self.bot.get_channel(reminder.channel_id)
            if channel:
                await channel.send(f"<@{reminder.user_id}>", embed=embed, view=view)
                return True
        except discord.Forbidden:
            log.debug(f"Missing permissions in original channel {reminder.channel_id}")
        except discord.HTTPException as e:
            log.debug(f"Failed to send to original channel: {str(e)}")
            
        return False

    async def _try_fallback_channels(self, guild: discord.Guild, user: discord.User, 
                                   embed: discord.Embed, view: View) -> bool:
        """Try common fallback channels in order"""
        if not guild:
            return False
            
        # Ordered list of channels to try
        fallback_channels = [
            "bot-spam",
            "general",
            "reminders",
            "chat"
        ]
        
        for channel_name in fallback_channels:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel:
                try:
                    # Check if we can send messages and mention the user
                    perms = channel.permissions_for(guild.me)
                    if perms.send_messages and perms.embed_links:
                        await channel.send(f"<@{user.id}>", embed=embed, view=view)
                        log.debug(f"Used fallback channel: {channel.name}")
                        return True
                except discord.HTTPException:
                    continue
                    
        return False

    async def _try_dm(self, user: discord.User, embed: discord.Embed, view: View) -> bool:
        """Final fallback to DM"""
        try:
            await user.send(embed=embed, view=view)
            return True
        except discord.Forbidden:
            log.debug(f"Could not DM user {user.id}")
            return False

    def create_reminder_embed(self, reminder: Reminder) -> discord.Embed:
        """Create embed for reminder delivery"""
        embed = discord.Embed(
            title="⏰ Reminder",
            description=f"```\n{reminder.text}\n```",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Created",
            value=discord.utils.format_dt(reminder.created_at, "R"),
            inline=False
        )
        if reminder.recurring:
            embed.add_field(
                name="Recurring",
                value=f"Every {reminder.recurring}",
                inline=False
            )
        embed.set_footer(text=f"Reminder ID: {reminder.id}")
        return embed

    async def shutdown(self):
        """Graceful shutdown"""
        self.reminder_loop.cancel()
        try:
            await asyncio.wait_for(self._processing_lock.acquire(), timeout=5.0)
        except asyncio.TimeoutError:
            log.warning("Forced shutdown during active processing")