# remind.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

import dateparser
import pytz
from dateutil.parser import parse

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button


log = logging.getLogger("Modmail")

# Timezone validation regex
UTC_OFFSET_PATTERN = re.compile(r'^UTC([+-])(\d{1,2})$', re.IGNORECASE)

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

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ CREATE_EMBED ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
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
            embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

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
            # Fallback embed if formatting fails
            embed = discord.Embed(
                description=f"### 📝 Reminder:\n{reminder_data['text']}",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"ID: {reminder_data['_id']} (Error: {str(e)[:50]})")
            return embed

    # ┌──────────────────────┬───────────────┬─────────────────────┐
    # ├──────────────────────┤ PREVIOUS_PAGE ├─────────────────────┤
    # └──────────────────────┴───────────────┴─────────────────────┘
    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)

    # ┌──────────────────────┬───────────┬─────────────────────────┐
    # ├──────────────────────┤ NEXT_PAGE ├─────────────────────────┤
    # └──────────────────────┴───────────┴─────────────────────────┘
    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_embed(interaction)

    # ┌─────────────────────┬─────────────────┬────────────────────┐
    # ├─────────────────────┤ DELETE_REMINDER ├────────────────────┤
    # └─────────────────────┴─────────────────┴────────────────────┘
    async def delete_reminder(self, interaction: discord.Interaction):
        """Handle reminder deletion with atomic database operations"""
        try:
            reminder_id = self.embeds[self.current_page].footer.text.split("ID: ")[1]

            # Atomic delete operation
            result = await self.cog.db.delete_one({"_id": reminder_id})

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
                    description="🗑️ **Reminder deleted!**\n\nYou have no more reminders.",
                    color=discord.Color.green()
                )
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

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ UPDATE_EMBED ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    async def update_embed(self, interaction: discord.Interaction, confirmation: str = None):
        """Update the embed with current page and optional confirmation message"""
        user = await self.cog.bot.fetch_user(self.user_id)
        embed = await self.create_embed({
            "_id": self.embeds[self.current_page].footer.text.split("ID: ")[1],
            "due": self.embeds[self.current_page].timestamp,
            "text": self.embeds[self.current_page].description.split("### 📝 Reminder:\n")[1]
        }, user)

        if confirmation:
            embed.set_footer(text=f"{confirmation}\n{embed.footer.text}")

        await interaction.response.edit_message(embed=embed, view=self)

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ ON_TIMEOUT ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
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

    # ┌───────────────────┬───────────────────┬────────────────────┐
    # ├───────────────────┤ INTERACTION_CHECK ├────────────────────┤
    # └───────────────────┴───────────────────┴────────────────────┘
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class TimezoneConverter(commands.Converter):
    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ CONVERT_FUNC ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    async def convert(self, ctx, argument):
        match = UTC_OFFSET_PATTERN.match(argument.strip())
        if not match:
            raise commands.BadArgument("Invalid timezone format. Use `UTC±HH` (e.g., `UTC+2`, `UTC-5`)")

        sign, hours = match.groups()
        try:
            hours = int(hours)
            if hours > 14 or hours < -12:
                raise commands.BadArgument("Timezone offset must be between UTC-12 and UTC+14")

            # Create a fixed offset timezone
            offset = hours * 60 * 60
            if sign == '-':
                offset = -offset
            return pytz.FixedOffset(offset / 60)
        except ValueError:
            raise commands.BadArgument("Invalid timezone format. Use `UTC±HH` (e.g., `UTC+2`, `UTC-5`)")

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

    def create_snooze_callback(self, minutes: int):
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
            ("daily", "Daily", "🔄"),
            ("weekly", "Weekly", "📅"), 
            ("monthly", "Monthly", "🗓️"),
            ("none", "One-time", "⏰")
        ]

        for freq, label, emoji in recurring_options:
            button = Button(
                label=f"{emoji} {label}",
                custom_id=f"recurring_{freq}_{user_id}_{datetime.now().timestamp()}",
                style=discord.ButtonStyle.secondary if freq != "none" else discord.ButtonStyle.primary
            )
            button.callback = self.create_recurring_callback(freq)
            self.add_item(button)

    def create_recurring_callback(self, frequency: str):
        """Create callback for specific recurring frequency"""
        async def recurring_callback(interaction: discord.Interaction):
            try:
                # Update reminder data
                if frequency != "none":
                    self.reminder_data["recurring"] = frequency

                # Save to database
                await self.cog.db.insert_one({
                    "user_id": self.user_id,
                    "channel_id": self.reminder_data["channel_id"],
                    "text": self.reminder_data["text"],
                    "due": self.reminder_data["due"],
                    "created": datetime.now(pytz.UTC),
                    "status": "active",
                    "recurring": frequency if frequency != "none" else None
                })

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

                # Disable all buttons
                for item in self.children:
                    item.disabled = True

                await interaction.response.edit_message(embed=embed, view=self)

            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Error setting reminder: {str(e)[:100]}",
                    ephemeral=True
                )

        return recurring_callback

    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class Remind(commands.Cog):
    """Remind plugin with timezone support"""

    async def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        from .remindertimezone import ReminderTimezone
        self.timezone_manager = ReminderTimezone(self.db)
        self.reminder_loop.start()

        # Create database indexes for performance
        try:
            await self.db.create_index([("user_id", 1), ("status", 1)])
            await self.db.create_index([("due", 1), ("status", 1)])
        except Exception as e:
            log.error(f"Failed to create indexes: {e}")

    def cog_unload(self):
        self.reminder_loop.cancel()

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ GET_USER_TZ  ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    async def get_user_timezone(self, user_id: int) -> pytz.FixedOffset:
        """Get user's timezone from DB or cache"""
        if user_id in self.user_timezones:
            return self.user_timezones[user_id]

        user_data = await self.db.find_one({"_id": f"timezone_{user_id}"})
        if user_data:
            tz = pytz.FixedOffset(user_data["offset_minutes"])
            self.user_timezones[user_id] = tz
            return tz

        # Default to UTC if not set
        return pytz.UTC

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ FORMAT_TIMEZ ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    async def format_time_with_timezone(self, dt: datetime, user_id: int) -> str:
        """Format time for display in user's timezone"""
        user_tz = await self.get_user_timezone(user_id)
        local_dt = dt.astimezone(user_tz)
        return (
            f"{discord.utils.format_dt(local_dt, 'f')}\n"
            f"({discord.utils.format_dt(local_dt, 'R')})"
        )

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░ SET_TIMEZONE_COMMAND ░░░░░░░░░░░░░░░░░░░║
    # ╚════════════════════════════════════════════════════════════╝
    @commands.command(name="mytimezone", aliases=["settimezone", "settz"])
    async def set_timezone(self, ctx, *, timezone_str: str):
        """Set your timezone (e.g., `!mytimezone UTC+2`)"""
        try:
            timezone = await self.timezone_manager.set_user_timezone(ctx.author.id, timezone_str)

            if not timezone:
                return await ctx.send(
                    "❌ **Invalid timezone format!**\n"
                    "Use `UTC±HH` format (e.g., `UTC+2`, `UTC-5`)\n"
                    "Offset must be between UTC-12 and UTC+14"
                )

            tz_display = self.timezone_manager.get_timezone_display(timezone)
            current_time = await self.timezone_manager.format_time_with_timezone(
                datetime.now(pytz.UTC), ctx.author.id
            )

            embed = discord.Embed(
                description=(
                    f"⏰ **Timezone updated!**\n\n"
                    f"**Timezone:** `{tz_display}`\n"
                    f"**Current time:** {current_time}"
                ),
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error setting timezone: {str(e)[:100]}")

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░ SHOW_TIMEZONE_CMD  ░░░░░░░░░░░░░░░░░░░░░║
    # ╚════════════════════════════════════════════════════════════╝
    @commands.command(name="mytime")
    async def show_current_time(self, ctx):
        """Show your current time based on your timezone setting"""
        try:
            user_tz = await self.timezone_manager.get_user_timezone(ctx.author.id)
            current_time = await self.timezone_manager.format_time_with_timezone(
                datetime.now(pytz.UTC), ctx.author.id
            )
            tz_display = self.timezone_manager.get_timezone_display(user_tz)

            embed = discord.Embed(
                description=(
                    f"⏰ **Your current time:**\n\n"
                    f"{current_time}\n"
                    f"**Timezone:** `{tz_display}`"
                ),
                color=discord.Color.blue()
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error fetching time: {str(e)[:100]}")

    @tasks.loop(seconds=60.0)
    async def reminder_loop(self):
        """Check reminders every minute with dual delivery system"""
        try:
            now = datetime.now(pytz.UTC)
            # Query with index-optimized filter
            reminders = await self.db.find({
                "due": {"$lte": now}, 
                "status": "active"
            }).to_list(100)  # Limit batch size

            for reminder in reminders:
                try:
                    user = self.bot.get_user(reminder["user_id"])
                    if not user:
                        # Mark as failed if user not found
                        await self.db.update_one(
                            {"_id": reminder["_id"]},
                            {"$set": {"status": "failed", "error": "user_not_found"}}
                        )
                        continue

                    # Format message with user's timezone
                    time_str = await self.timezone_manager.format_time_with_timezone(
                        reminder["due"], reminder["user_id"]
                    )

                    message = (
                        f"⏰ **Reminder** ({time_str})\n"
                        f"{reminder['text']}"
                    )

                    # Dual delivery system: try channel first, then DM
                    delivery_success = False

                    # Try original channel
                    if reminder.get("channel_id"):
                        try:
                            channel = self.bot.get_channel(reminder["channel_id"])
                            if channel:
                                # Create snooze view for channel delivery
                                snooze_view = SnoozeView(self, str(reminder["_id"]), reminder["user_id"])
                                await channel.send(f"{user.mention} {message}", view=snooze_view)
                                delivery_success = True
                        except Exception as channel_error:
                            log.warning(f"Channel delivery failed for reminder {reminder['_id']}: {channel_error}")

                    # Fallback to DM if channel failed or unavailable
                    if not delivery_success:
                        try:
                            snooze_view = SnoozeView(self, str(reminder["_id"]), reminder["user_id"])
                            await user.send(message, view=snooze_view)
                            delivery_success = True
                        except Exception as dm_error:
                            log.warning(f"DM delivery failed for reminder {reminder['_id']}: {dm_error}")

                    # Handle post-delivery actions
                    if delivery_success:
                        if reminder.get("recurring"):
                            await self._reschedule_recurring(reminder)
                        else:
                            await self.db.update_one(
                                {"_id": reminder["_id"]},
                                {"$set": {"status": "completed", "delivered": now}}
                            )
                    else:
                        # Mark as failed with retry logic
                        retry_count = reminder.get("retry_count", 0)
                        if retry_count < 3:
                            # Retry in 5 minutes
                            await self.db.update_one(
                                {"_id": reminder["_id"]},
                                {
                                    "$set": {
                                        "due": now + timedelta(minutes=5),
                                        "retry_count": retry_count + 1
                                    }
                                }
                            )
                        else:
                            await self.db.update_one(
                                {"_id": reminder["_id"]},
                                {"$set": {"status": "failed", "error": "delivery_failed"}}
                            )

                except Exception as reminder_error:
                    log.error(f"Error processing reminder {reminder.get('_id', 'unknown')}: {reminder_error}")

            # Clean timezone cache every hour (when minute is 0)
            if now.minute == 0:
                active_users = set()
                async for reminder in self.db.find({"status": "active"}, {"user_id": 1}):
                    active_users.add(reminder["user_id"])
                self.timezone_manager.clean_cache(active_users)

        except Exception as e:
            log.error(f"Reminder loop error: {e}")

    # ┌──────────────────┬──────────────────────┬──────────────────┐
    # ├──────────────────┤ RESCHEDULE_RECURRING ├──────────────────┤
    # └──────────────────┴──────────────────────┴──────────────────┘
    async def _reschedule_recurring(self, reminder: dict):
        """Reschedule recurring reminders maintaining original time-of-day"""
        try:
            frequency = reminder["recurring"]
            original_due = reminder["due"]

            # Calculate next occurrence maintaining time-of-day
            if frequency == "daily":
                next_due = original_due + timedelta(days=1)
            elif frequency == "weekly":
                next_due = original_due + timedelta(weeks=1)
            elif frequency == "monthly":
                # Handle month boundaries properly
                if original_due.month == 12:
                    next_due = original_due.replace(year=original_due.year + 1, month=1)
                else:
                    try:
                        next_due = original_due.replace(month=original_due.month + 1)
                    except ValueError:
                        # Handle cases like Jan 31 -> Feb (no 31st)
                        next_due = original_due.replace(month=original_due.month + 1, day=28)
            else:
                log.error(f"Unknown recurring frequency: {frequency}")
                return

            # Atomic update to reschedule
            await self.db.update_one(
                {"_id": reminder["_id"]},
                {
                    "$set": {
                        "due": next_due,
                        "status": "active"
                    },
                    "$unset": {"retry_count": ""}
                }
            )

        except Exception as e:
            log.error(f"Failed to reschedule recurring reminder {reminder.get('_id')}: {e}")
            # Mark as failed if rescheduling fails
            await self.db.update_one(
                {"_id": reminder["_id"]},
                {"$set": {"status": "failed", "error": "reschedule_failed"}}
            )

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░ REMINDME_COMMAND   ░░░░░░░░░░░░░░░░░░░░░║
    # ╚════════════════════════════════════════════════════════════╝
    @commands.command(aliases=["remindme"])
    async def remind(self, ctx, *, input_string: str):
        """Set a reminder - Usage: `!remind [time] SEPARATOR [text]`

        Supported separators: | , - . / > [ to
        Examples:
        • `!remind in 2 hours | take out the trash`
        • `!remind tomorrow at 3pm - buy groceries`
        • `!remind next monday, finish the report`
        """
        try:
            # Parse input (existing logic)
            SEPARATORS = [" to ", " | ", " - ", " / ", " > ", " [", " — ", ", "]

            separator = None
            for sep in SEPARATORS:
                if sep in input_string:
                    separator = sep
                    break

            if not separator:
                return await ctx.send(
                    "⚠️ **Missing separator!**\n"
                    "Please split the time and reminder text with one of these:\n"
                    "`|` `-` `,` `.` `/` `>` `[` `to`\n\n"
                    "**Example:**\n"
                    "`!remind in 2 hours | take out the trash`"
                )

            time_part, reminder_text = input_string.split(separator, 1)
            reminder_text = reminder_text.strip()

            if not reminder_text:
                return await ctx.send("⚠️ Reminder text cannot be empty!")

            # Parse time with user's timezone
            user_tz = await self.timezone_manager.get_user_timezone(ctx.author.id)
            settings = {
                'RELATIVE_BASE': datetime.now(user_tz),
                'TIMEZONE': str(user_tz),
                'TO_TIMEZONE': 'UTC'
            }
            due = dateparser.parse(time_part, settings=settings)

            if not due:
                return await ctx.send(
                    "⚠️ Couldn't understand the time. Try formats like:\n"
                    "• `in 5 minutes`\n• `tomorrow at 3pm`\n• `next monday`"
                )

            # Ensure UTC timezone
            due = pytz.UTC.localize(due) if due.tzinfo is None else due.astimezone(pytz.UTC)

            # Validate future time
            if due <= datetime.now(pytz.UTC):
                current_time_str = await self.timezone_manager.format_time_with_timezone(
                    datetime.now(pytz.UTC), ctx.author.id
                )
                entered_time_str = await self.timezone_manager.format_time_with_timezone(
                    due, ctx.author.id
                )
                return await ctx.send(
                    f"⏳ **Time must be in the future!**\n"
                    f"You entered: `{entered_time_str}`\n"
                    f"Current time: `{current_time_str}`"
                )

            # Show recurring options
            reminder_data = {
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "text": reminder_text,
                "due": due
            }

            time_str = await self.timezone_manager.format_time_with_timezone(due, ctx.author.id)

            embed = discord.Embed(
                description=(
                    f"⏰ **Set reminder for:**\n\n"
                    f"**When:** {time_str}\n"
                    f"**Reminder:** {reminder_text}\n\n"
                    f"**Choose frequency:**"
                ),
                color=discord.Color.blue()
            )

            view = RecurringView(self, ctx.author.id, reminder_data)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            await ctx.send(
                f"❌ **Error setting reminder:** {str(e)[:100]}\n\n"
                "**Proper Usage Examples:**\n"
                "• `!remind in 2 hours | take out the trash`\n"
                "• `!remind tomorrow at 3pm - buy groceries`"
            )

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░ REMINDERS          ░░░░░░░░░░░░░░░░░░░░░║
    # ╚════════════════════════════════════════════════════════════╝
    @commands.command(aliases=["myreminders", "mr"])
    async def reminders(self, ctx):
        """List your active reminders in a paginated embed"""
        try:
            # Fetch reminders from database
            reminders = await self.db.find(
                {"user_id": ctx.author.id, "status": "active"}
            ).sort("due", 1).to_list(None)  # Sort by due date ascending

            if not reminders:
                embed = discord.Embed(
                    description="⏰ You have no active reminders!",
                    color=0x00ff00
                )
                return await ctx.send(embed=embed)

            # Create paginated embeds
            embeds = []
            for idx, rem in enumerate(reminders, 1):
                # Get user's timezone for display
                user_tz = await self.get_user_timezone(ctx.author.id)
                local_dt = rem["due"].astimezone(user_tz)

                embed = discord.Embed(
                    description=f"### 📝 Reminder:\n{rem['text']}",
                    color=discord.Color(0xd0d88f),
                    timestamp=rem["due"]
                )

                # Set author with user's avatar
                embed.set_author(
                    name=f"⏰ Reminder #{idx} for {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url
                )

                # Set thumbnail
                embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

                # Add formatted time field
                time_str = (
                    f"```cs\n"
                    f"{local_dt.strftime('%d %B %Y %H:%M')}\n"
                    f"[{discord.utils.format_dt(rem['due'], 'R')}]\n"
                    f"```"
                )
                embed.add_field(
                    name="📆 When:",
                    value=time_str,
                    inline=False
                )

                # Add footer with ID
                embed.set_footer(text=f"ID: {rem['_id']}")

                embeds.append(embed)

            # Send paginated view
            message = await ctx.send(embed=embeds[0])
            paginator = ReminderPaginator(embeds, ctx.author.id, message, self)
            await message.edit(view=paginator)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error fetching reminders",
                description=f"```{str(e)[:1000]}```",  # Truncate long errors
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Remind(bot))
