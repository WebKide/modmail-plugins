# remindercore.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Awaitable
import re

import pytz
from dateutil.relativedelta import relativedelta

import discord
from discord import Interaction
from discord.ext import commands
from discord.ui import View, Button

log = logging.getLogger("Modmail")
logo = "https://i.imgur.com/677JpTl.png"

class ReminderPaginator(View):
    """Enhanced paginator for reminder lists with delete functionality"""
    def __init__(self, embeds: List[discord.Embed], user_id: int, original_message: discord.Message, cog):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.original_message = original_message
        self.deleted = False
        self.cog = cog
        self.delete_task = None
        self.add_buttons()

        # Start delete timer if not in DMs
        if not isinstance(original_message.channel, (discord.DMChannel, discord.PartialMessageable)):
            self.delete_task = self.cog.bot.loop.create_task(self.delete_after_delay())

    def add_buttons(self):
        """Add navigation and action buttons based on current state"""
        self.clear_items()  # Clear existing buttons

        # Navigation buttons (only if multiple pages)
        if len(self.embeds) > 1:
            # Previous button
            prev_button = Button(
                label="◀",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_page == 0
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

            # Page indicator
            page_button = Button(
                label=f"{self.current_page + 1}/{len(self.embeds)}",
                style=discord.ButtonStyle.secondary,
                disabled=True
            )
            self.add_item(page_button)

            # Next button
            next_button = Button(
                label="▶",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_page == len(self.embeds) - 1
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

        # Action buttons
        delete_button = Button(
            label="🗑️ Delete",
            style=discord.ButtonStyle.danger
        )
        delete_button.callback = self.delete_reminder
        self.add_item(delete_button)

        off_button = Button(
            label="OFF",
            emoji="🔇",
            style=discord.ButtonStyle.secondary
        )
        off_button.callback = self.off_reminder
        self.add_item(off_button)

    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.add_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next_page(self, interaction: discord.Interaction):
        """Navigate to next page"""
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.add_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def delete_after_delay(self, delay=60):
        """Delete the message after delay if not in DMs"""
        try:
            await asyncio.sleep(delay)
            if not self.deleted:
                await self.original_message.delete()
                self.deleted = True
        except asyncio.CancelledError:
            pass  # Task was cancelled, this is expected
        except Exception as e:
            log.error(f"Error in delete_after_delay: {e}")

    async def on_timeout(self):
        """Gracefully disable buttons when view times out"""
        if self.deleted:
            return

        try:
            # Cancel delete task if it exists
            if self.delete_task and not self.delete_task.done():
                self.delete_task.cancel()

            # Disable all buttons
            for item in self.children:
                item.disabled = True

            await self.original_message.edit(view=self)
        except discord.NotFound:
            pass  # Message was already deleted
        except Exception as e:
            log.error(f"Error in ReminderPaginator timeout: {e}")

    # Updated delete_reminder block
    async def delete_reminder(self, interaction: discord.Interaction):
        """Handle reminder deletion with proper atomic operations and error handling"""
        try:
            if not self.embeds:
                await interaction.response.send_message("❌ No reminders to delete", ephemeral=True)
                return

            # Get reminder ID from stored data (safer than parsing footer)
            reminder_data = self.embeds[self.current_page].footer.text
            reminder_id = reminder_data.split("ID: ")[1].split(" ")[0]  # Fallback parsing
            try:
                # Fetch reminder from database to verify existence
                reminder = await self.cog.db.find_one({"_id": reminder_id, "status": "active"})
                if not reminder:
                    await interaction.response.send_message("❌ Reminder not found (may have been already deleted)", ephemeral=True)
                    return
            except Exception as e:
                log.error(f"Database error fetching reminder {reminder_id}: {e}")
                await interaction.response.send_message(f"❌ Database error: Connection failed", ephemeral=True)
                return

            # Atomic delete operation
            result = await self.cog.db.delete_one({"_id": reminder_id, "status": "active"})
            if result.deleted_count == 0:
                await interaction.response.send_message("❌ Reminder not found (may have been already deleted)", ephemeral=True)
                return

            # Remove from local list
            del self.embeds[self.current_page]

            if not self.embeds:
                # No reminders left - create final embed
                embed = discord.Embed(
                    description="## 🗑️ **Reminder deleted!**\n\nYou have no more reminders.",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=logo)

                # Cancel delete task and mark as deleted
                if self.delete_task and not self.delete_task.done():
                    self.delete_task.cancel()
                self.deleted = True

                await interaction.response.edit_message(embed=embed, view=None)
                return

            # Adjust current page if needed
            if self.current_page >= len(self.embeds):
                self.current_page = len(self.embeds) - 1

            # Update buttons for new page count
            self.add_buttons()

            # Update display with current page
            await self.update_embed(interaction, "🗑️ Reminder deleted!")

        except Exception as e:
            log.error(f"Unexpected error in delete_reminder: {e}")
            await interaction.response.send_message(f"❌ Unexpected error: Please try again", ephemeral=True)

    async def update_embed(self, interaction: discord.Interaction, confirmation: str = None):
        """Update the embed with current page and optional confirmation message"""
        try:
            # Extract reminder data from current embed
            current_embed = self.embeds[self.current_page]
            reminder_id = current_embed.footer.text.split("ID: ")[1].split(" ")[0]  # Handle error text

            # Parse description to get reminder text
            description_lines = current_embed.description.split("\n")
            reminder_text = "\n".join(description_lines[1:]) if len(description_lines) > 1 else "Reminder text unavailable"

            # Get recurring status from fields
            recurring = None
            for field in current_embed.fields:
                if field.name == "🔄 Recurring:":
                    recurring = field.value.strip("`").lower()
                    break

            reminder_data = {
                "_id": reminder_id,
                "due": current_embed.timestamp,
                "text": reminder_text,
                "recurring": recurring
            }

            user = await self.cog.bot.fetch_user(self.user_id)
            embed = await self.create_embed(reminder_data, user)

            if confirmation:
                embed.set_footer(text=f"{confirmation}\n{embed.footer.text}")

            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            log.error(f"Error updating embed: {e}")
            await interaction.response.send_message(
                f"❌ Error updating display: {str(e)[:100]}",
                ephemeral=True
            )

    async def off_reminder(self, interaction: discord.Interaction):
        """Turn off the reminder display without deleting the reminder"""
        try:
            await interaction.response.edit_message(
                content="🔇 Reminder display turned off",
                embed=None,
                view=None
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error turning off reminder: {str(e)[:100]}",
                ephemeral=True
            )

    async def on_timeout(self):
        """Gracefully disable buttons when view times out"""
        if not self.deleted:
            try:
                # Disable all buttons
                for item in self.children:
                    item.disabled = True

                # Update message with disabled buttons
                await self.original_message.edit(view=self)
            except discord.NotFound:
                pass  # Message was deleted
            except Exception as e:
                log.error(f"Error in ReminderPaginator timeout: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class SnoozeView(View):
    """Snooze buttons for delivered reminders"""

    def __init__(self, cog, reminder_id: str, user_id: int):
        super().__init__(timeout=600)  # 10 minute timeout
        self.cog = cog
        self.reminder_id = reminder_id
        self.user_id = user_id

        # Add snooze buttons with different durations
        snooze_options = [
            (30, "30m", discord.ButtonStyle.secondary),
            (60, "1h", discord.ButtonStyle.primary),
            (1440, "1d", discord.ButtonStyle.success)
        ]

        for minutes, label, style in snooze_options:
            button = Button(
                label=label,
                custom_id=f"snooze_{minutes}_{user_id}_{datetime.now().timestamp()}",
                style=style
            )
            button.callback = self.create_snooze_callback(minutes)
            self.add_item(button)

    def create_snooze_callback(self, minutes: int) -> Callable[[discord.Interaction], Awaitable[None]]:
        """Create callback for specific snooze duration"""
        async def snooze_callback(interaction: discord.Interaction):
            try:
                new_due = datetime.now(pytz.UTC) + timedelta(minutes=minutes)

                # Update reminder in database atomically
                result = await self.cog.db.update_one(
                    {"_id": self.reminder_id, "status": "active"},
                    {"$set": {"due": new_due, "status": "active"}}
                )

                if result.modified_count > 0:
                    time_str = await self.cog.timezone_manager.format_time_with_timezone(
                        new_due, self.user_id
                    )

                    embed = discord.Embed(
                        description=f"⏰ **Reminder snoozed!**\n\nNew time: {time_str}",
                        color=discord.Color.green()
                    )
                    # Set thumbnail
                    embed.set_thumbnail(url=logo)
                    # Disable all buttons
                    for item in self.children:
                        item.disabled = True

                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await interaction.response.send_message(
                        "❌ Failed to snooze reminder (may have been deleted)",
                        ephemeral=True
                    )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Error snoozing reminder: {str(e)[:100]}",
                    ephemeral=True
                )

        return snooze_callback

    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id


class RecurringView(View):
    """View for setting recurring reminder options"""

    def __init__(self, cog, user_id: int, reminder_data: dict):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.user_id = user_id
        self.reminder_data = reminder_data

        # Add recurring option buttons
        recurring_options = [
            ("daily", "Daily", "🔄", discord.ButtonStyle.secondary),
            ("weekly", "Weekly", "📅", discord.ButtonStyle.secondary), 
            ("monthly", "Monthly", "🗓️", discord.ButtonStyle.secondary),
            ("none", "One-time", "⏰", discord.ButtonStyle.primary)
        ]

        for freq, label, emoji, style in recurring_options:
            button = Button(
                label=f"{emoji} {label}",
                style=style,
                custom_id=f"recurring_{freq}_{user_id}_{datetime.now().timestamp()}"
            )
            button.callback = self.create_recurring_callback(freq)
            self.add_item(button)

    def create_recurring_callback(self, frequency: str):
        """Create callback for specific recurring frequency"""
        async def callback(interaction: discord.Interaction):
            try:
                # Generate unique ID for reminder
                import uuid
                reminder_id = str(uuid.uuid4())

                # Prepare reminder document
                reminder_doc = {
                    "_id": reminder_id,
                    "user_id": self.user_id,
                    "channel_id": self.reminder_data["channel_id"],
                    "guild_id": self.reminder_data.get("guild_id"),
                    "text": self.reminder_data["text"],
                    "due": self.reminder_data["due"],
                    "created": datetime.now(pytz.UTC),
                    "status": "active"
                }

                # Add recurring field if not one-time
                if frequency != "none":
                    reminder_doc["recurring"] = frequency

                # Atomic database operation
                try:
                    await self.cog.db.insert_one(reminder_doc)
                except Exception as e:
                    log.error(f"Database error creating reminder: {e}")
                    await interaction.response.send_message("❌ Database error: Could not save reminder", ephemeral=True)
                    return

                # Format confirmation message
                time_str = await self.cog.timezone_manager.format_time_with_timezone(
                    self.reminder_data["due"], self.user_id
                )

                recurring_text = "" if frequency == "none" else f"\n🔄 **Recurring:** {frequency.title()}"

                embed = discord.Embed(
                    description=(
                        f"✅ **Reminder set!**\n\n"
                        f"**When:** {time_str}\n"
                        f"**Reminder:** {self.reminder_data['text']}"
                        f"{recurring_text}"
                    ),
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=logo)

                # Disable all buttons
                for item in self.children:
                    item.disabled = True

                await interaction.response.edit_message(embed=embed, view=self)

            except Exception as e:
                log.error(f"Unexpected error in recurring callback: {e}")
                await interaction.response.send_message("❌ Unexpected error: Please try again", ephemeral=True)

        return callback

    async def on_timeout(self):
        """Disable buttons when view times out"""
        try:
            for item in self.children:
                item.disabled = True
            # Don't try to edit if we can't find the original message
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception as e:
            log.error(f"Error in RecurringView timeout: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class DualDeliveryView(View):
    """View with both Snooze and OFF buttons for reminders"""

    def __init__(self, cog, reminder_id: str, user_id: int):
        super().__init__(timeout=600)  # 10 minute timeout
        self.cog = cog
        self.reminder_id = reminder_id
        self.user_id = user_id

        # Snooze buttons
        snooze_options = [
            (30, "30m", discord.ButtonStyle.secondary),
            (60, "1h", discord.ButtonStyle.primary),
            (1440, "1d", discord.ButtonStyle.success)
        ]

        for minutes, label, style in snooze_options:
            button = Button(
                label=label,
                custom_id=f"snooze_{minutes}_{user_id}_{datetime.now().timestamp()}",
                style=style
            )
            button.callback = self.create_snooze_callback(minutes)
            self.add_item(button)

        # OFF button
        off_button = Button(
            label="OFF",
            emoji="🔇",
            style=discord.ButtonStyle.danger,
            custom_id=f"off_{user_id}_{datetime.now().timestamp()}"
        )
        off_button.callback = self.off_callback
        self.add_item(off_button)

    def create_snooze_callback(self, minutes: int):
        """Create callback for specific snooze duration"""
        async def callback(interaction: discord.Interaction):
            try:
                new_due = datetime.now(pytz.UTC) + timedelta(minutes=minutes)
                await self.cog.db.update_one(
                    {"_id": self.reminder_id},
                    {"$set": {"due": new_due}}
                )

                time_str = await self.cog.timezone_manager.format_time_with_timezone(
                    new_due, self.user_id
                )

                await interaction.response.edit_message(
                    content=f"⏰ Reminder snoozed until {time_str}",
                    embed=None,
                    view=None
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Error snoozing reminder: {str(e)[:100]}",
                    ephemeral=True
                )
        return callback

    async def off_callback(self, interaction: discord.Interaction):
        """Delete the reminder message without affecting the reminder itself"""
        try:
            await interaction.response.edit_message(
                content="🔇 Reminder message turned off",
                embed=None,
                view=None
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error turning off reminder: {str(e)[:100]}",
                ephemeral=True
            )

    async def on_timeout(self):
        """When buttons time out, safely handle message cleanup"""
        try:
            # Check if we have a valid message reference
            if not hasattr(self, 'message') or not self.message:
                return

            # Disable all buttons first
            for item in self.children:
                item.disabled = True

            # Try to edit the message to remove buttons
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                # Message was deleted, that's fine
                return
            except discord.HTTPException:
                # Other HTTP errors, log but continue
                log.warning(f"Could not edit message in DualDeliveryView timeout")

            # Only add reaction if we're not in DMs and message still exists
            if not isinstance(self.message.channel, discord.DMChannel):
                try:
                    await self.message.add_reaction("✅")
                except Exception as e:
                    log.debug(f"Could not add reaction in DualDeliveryView: {e}")

        except Exception as e:
            log.error(f"Error in DualDeliveryView timeout: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id
