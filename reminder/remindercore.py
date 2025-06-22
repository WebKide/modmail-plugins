# remindercore.py
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

class ReminderPaginator(View):
    """Enhanced paginator for reminder lists with delete functionality"""
    def __init__(self, embeds: List[discord.Embed], user_id: int, original_message: discord.Message, cog):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.original_message = original_message
        self.deleted = False
        self.cog = cog  # Reference to the main cog for DB access

        # Add buttons
        self.add_buttons()

    def add_buttons(self):
        """Dynamically add buttons based on page count"""
        # Clear existing buttons
        self.clear_items()

        # Previous button
        if len(self.embeds) > 1:
            prev_button = Button(
                emoji="⬅️",
                style=discord.ButtonStyle.blurple,
                custom_id=f"prev_{self.user_id}_{datetime.now().timestamp()}"
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

        # Delete button
        delete_button = Button(
            emoji="🗑️",
            style=discord.ButtonStyle.red,
            custom_id=f"delete_{self.user_id}_{datetime.now().timestamp()}"
        )
        delete_button.callback = self.delete_reminder
        self.add_item(delete_button)

        # Next button
        if len(self.embeds) > 1:
            next_button = Button(
                emoji="➡️",
                style=discord.ButtonStyle.blurple,
                custom_id=f"next_{self.user_id}_{datetime.now().timestamp()}"
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def create_embed(self, reminder_data: dict, user: discord.User) -> discord.Embed:
        """Create a styled embed for a reminder using centralized timezone handling"""
        try:
            time_str = await self.cog.timezone_manager.format_time_with_timezone(
                reminder_data["due"], self.user_id
            )

            embed = discord.Embed(
                description=f"### 📝 Reminder:\n{reminder_data['text']}",
                color=discord.Color(0xd0d88f),
                timestamp=reminder_data["due"]
            )

            # Set author with user's avatar
            embed.set_author(
                name=f"⏰ Reminder #{self.current_page + 1} for {user.display_name}",
                icon_url=user.avatar.url if user.avatar else user.default_avatar.url
            )

            # Set thumbnail
            embed.set_thumbnail(url="https://i.imgur.com/677JpTl.png")

            # Add formatted time field
            embed.add_field(
                name="📆 When:",
                value=f"```cs\n{time_str}\n```",
                inline=False
            )

            # Add recurring info if applicable
            if reminder_data.get("recurring"):
                embed.add_field(
                    name="🔄 Recurring:",
                    value=f"`{reminder_data['recurring'].title()}`",
                    inline=True
                )

            # Add footer with ID
            embed.set_footer(text=f"ID: {reminder_data['_id']}")

            return embed

        except Exception as e:
            log.error(f"Error creating reminder embed: {e}")
            # Fallback embed if formatting fails
            embed = discord.Embed(
                description=f"### 📝 Reminder:\n{reminder_data['text']}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://i.imgur.com/677JpTl.png")
            embed.set_footer(text=f"ID: {reminder_data['_id']} (Error: {str(e)[:50]})")
            return embed

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_embed(interaction)

    async def delete_reminder(self, interaction: discord.Interaction):
        """Handle reminder deletion with atomic database operations"""
        try:
            if not self.embeds:
                await interaction.response.send_message(
                    "❌ No reminders to delete",
                    ephemeral=True
                )
                return

            try:
                reminder_id = self.embeds[self.current_page].footer.text.split("ID: ")[1]
            except (IndexError, AttributeError):
                await interaction.response.send_message(
                    "❌ Could not find reminder ID",
                    ephemeral=True
                )
                return

            # Atomic delete operation
            try:
                result = await self.cog.db.delete_one({"_id": reminder_id})
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Database error: {str(e)[:100]}",
                    ephemeral=True
                )
                return

            if result.deleted_count == 0:
                await interaction.response.send_message(
                    "❌ Reminder not found (may have been already deleted)",
                    ephemeral=True
                )
                return

            # Remove from local list
            del self.embeds[self.current_page]

            if not self.embeds:
                # No reminders left
                embed = discord.Embed(
                    description="## 🗑️ **Reminder deleted!**\n\nYou have no more reminders.",
                    color=discord.Color.green()
                )
                # Set thumbnail
                embed.set_thumbnail(url="https://i.imgur.com/677JpTl.png")
                self.deleted = True
                await interaction.response.edit_message(embed=embed, view=None)
                return

            # Adjust current page if needed
            if self.current_page >= len(self.embeds):
                self.current_page = len(self.embeds) - 1

            # Update buttons and embed
            self.add_buttons()

            # Get current reminder data for display
            current_embed = self.embeds[self.current_page]
            reminder_data = {
                "_id": current_embed.footer.text.split("ID: ")[1],
                "due": current_embed.timestamp,
                "text": current_embed.description.split("### 📝 Reminder:\n")[1],
                "recurring": None
            }

            # Check if reminder is recurring
            for field in current_embed.fields:
                if field.name == "🔄 Recurring:":
                    reminder_data["recurring"] = field.value.strip("`").lower()
                    break

            user = await self.cog.bot.fetch_user(self.user_id)
            embed = await self.create_embed(reminder_data, user)
            embed.set_footer(text=f"🗑️ Reminder deleted!\n{embed.footer.text}")

            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting reminder: {str(e)[:100]}",
                ephemeral=True
            )

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
                    embed.set_thumbnail(url="https://i.imgur.com/677JpTl.png")
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
                # Update reminder data
                reminder_data = {
                    "user_id": self.user_id,
                    "channel_id": self.reminder_data["channel_id"],
                    "text": self.reminder_data["text"],
                    "due": self.reminder_data["due"],
                    "created": datetime.now(pytz.UTC),
                    "status": "active",
                    "recurring": frequency if frequency != "none" else None
                }

                # Save to database
                await self.cog.db.insert_one(reminder_data)

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
                # Set thumbnail
                embed.set_thumbnail(url="https://i.imgur.com/677JpTl.png")

                # Disable all buttons
                for item in self.children:
                    item.disabled = True

                await interaction.response.edit_message(embed=embed, view=self)

            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Error setting reminder: {str(e)[:100]}",
                    ephemeral=True
                )
        return callback

    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id
