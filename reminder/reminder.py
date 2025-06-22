# reminder.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

import dateparser
import pytz
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from core import checks
from core.models import PermissionLevel

from .remindertimezone import ReminderTimezone, TimezoneConverter
from .remindercore import ReminderPaginator, SnoozeView, RecurringView

log = logging.getLogger("Modmail")
__version__ = "3.03"
logo = "https://i.imgur.com/677JpTl.png"

class Reminder(commands.Cog):
    """Reminder plugin with timezone support"""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.timezone_manager = ReminderTimezone(self.db)
        self.reminder_loop.start()

        # Create database indexes for performance
        self.bot.loop.create_task(self._create_indexes())

    async def _create_indexes(self):
        try:
            await self.db.create_index([("user_id", 1), ("status", 1)])
            await self.db.create_index([("due", 1), ("status", 1)])
        except Exception as e:
            log.error(f"Failed to create indexes: {e}")

    def cog_unload(self):
        self.reminder_loop.cancel()

    async def get_user_timezone(self, user_id: int):
        """Get user timezone - wrapper for timezone manager"""
        return await self.timezone_manager.get_user_timezone(user_id)

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
                await msg.delete(delay=60)  # delete embed after a minute
                return

            tz_display = self.timezone_manager.get_timezone_display(timezone)
            current_time = await self.timezone_manager.format_time_with_timezone(
                datetime.now(pytz.UTC), ctx.author.id
            )

            embed = discord.Embed(
                description=(
                    f"### ⏰ **Timezone updated!**\n"
                    f"# **Timezone:** `{tz_display}`\n"
                    f"**Current time:** {current_time}"
                ),
                color=discord.Color.green()
            )
            # Set thumbnail
            embed.set_thumbnail(url=logo)

            msg = await ctx.send(embed=embed)
            await msg.delete(delay=60)  # delete embed after a minute

        except Exception as e:
            msg = await ctx.send(f"❌ Error setting timezone: {str(e)[:100]}")
            await msg.delete(delay=60)  # delete embed after a minute

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░ SHOW_CURRENT_TIMEZONE ░░░░░░░░░░░░░░░░░░░░║
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
                    f"## ⏰ **Your current time:**\n"
                    f"# {current_time}\n"
                    f"**Timezone:** `{tz_display}` set by user"
                ),
                color=discord.Color.blue()
            )
            # Set thumbnail
            embed.set_thumbnail(url=logo)

            msg = await ctx.send(embed=embed)
            await msg.delete(delay=60)  # delete embed after a minute

        except Exception as e:
            msg = await ctx.send(f"❌ Error fetching time: {str(e)[:100]}")
            await msg.delete(delay=60)  # delete embed after a minute

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ TASK_LOOP_60 ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    @tasks.loop(seconds=60.0)
    async def reminder_loop(self):
        """Check reminders every minute with batch processing"""
        try:
            await self.bot.wait_until_ready()  # Ensure bot is ready

            now = datetime.now(pytz.UTC)
            # Batch process reminders in chunks
            async for batch in self._get_reminder_batches(now):
                await self._process_reminder_batch(batch, now)

            # Clean cache hourly
            if now.minute == 0:
                await self._clean_timezone_cache()

        except Exception as e:
            log.error(f"Reminder loop error: {e}", exc_info=True)

    # ┌─────────────────────┬───────────────┬──────────────────────┐
    # ├─────────────────────┤ REMINDER_LOOP ├──────────────────────┤
    # └─────────────────────┴───────────────┴──────────────────────┘
    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        """Wait for bot to be ready before starting reminder loop"""
        await self.bot.wait_until_ready()

    async def _get_reminder_batches(self, now: datetime):
        """Yield batches of 50 reminders at a time"""
        query = {"due": {"$lte": now}, "status": "active"}
        cursor = self.db.find(query).sort("due", 1).batch_size(50)

        while True:
            batch = await cursor.to_list(length=50)
            if not batch:
                break
            yield batch

    async def _process_single_reminder(self, reminder: dict, now: datetime):
        """Process a single reminder delivery to both DM and channel with fallback"""
        try:
            # Get user
            user = self.bot.get_user(reminder["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(reminder["user_id"])
                except discord.NotFound:
                    # User not found - delete all reminders for this user
                    await self.db.delete_many({"user_id": reminder["user_id"], "status": "active"})
                    return

            # Prepare the reminder embed
            time_str = await self.timezone_manager.format_time_with_timezone(
                reminder["due"], reminder["user_id"]
            )

            embed = discord.Embed(
                description=f"### ⏰ **Reminder!**\n# {reminder['text']}",
                color=discord.Color.orange(),
                timestamp=reminder["due"]
            )
            embed.set_author(
                name=f"Reminder for {user.display_name}",
                icon_url=user.avatar.url if user.avatar else user.default_avatar.url
            )
            embed.add_field(
                name="📅 Originally set for:",
                value=f"```cs\n{time_str}\n```",
                inline=False
            )
            embed.set_thumbnail(url=logo)

            # Create view with Snooze and OFF buttons
            view = DualDeliveryView(self, reminder["_id"], reminder["user_id"])

            # Track delivery status
            delivery_status = {
                "dm_success": False,
                "channel_success": False,
                "dm_error": None,
                "channel_error": None
            }

            # Try DM delivery first
            try:
                await user.send(embed=embed, view=view)
                delivery_status["dm_success"] = True
            except discord.Forbidden:
                delivery_status["dm_error"] = "User disabled DMs"
            except Exception as e:
                delivery_status["dm_error"] = str(e)[:100]

            # Try original channel delivery
            channel = None
            try:
                channel = self.bot.get_channel(reminder["channel_id"])
                if not channel:
                    channel = await self.bot.fetch_channel(reminder["channel_id"])

                if isinstance(channel, (discord.DMChannel, discord.PartialMessageable)):
                    await channel.send(f"{user.mention}", embed=embed, view=view)
                else:
                    msg = await channel.send(f"{user.mention}", embed=embed, view=view)
                    await msg.delete(delay=60)
                # await channel.send(f"{user.mention}", embed=embed, view=view)
                delivery_status["channel_success"] = True
            except discord.Forbidden:
                delivery_status["channel_error"] = "Missing permissions in channel"
            except discord.NotFound:
                delivery_status["channel_error"] = "Channel not found"
            except Exception as e:
                delivery_status["channel_error"] = str(e)[:100]

            # Fallback to main guild channel if both failed and user is in guild
            if not delivery_status["dm_success"] and not delivery_status["channel_success"]:
                guild = self.bot.get_guild(reminder.get("guild_id"))
                if guild:
                    try:
                        # Find first text channel we can send to
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                # Modify embed to show delivery issues
                                footer_text = []
                                if delivery_status["dm_error"]:
                                    footer_text.append(f"DM failed: {delivery_status['dm_error']}")
                                if delivery_status["channel_error"]:
                                    footer_text.append(f"Original channel failed: {delivery_status['channel_error']}")

                                embed.set_footer(text=" | ".join(footer_text))
                                await ch.send(f"{user.mention}", embed=embed, view=view)
                                break
                    except Exception:
                        pass

            # Handle recurring or mark as completed
            if reminder.get("recurring"):
                await self._reschedule_recurring(reminder)
            else:
                await self.db.update_one(
                    {"_id": reminder["_id"]},
                    {"$set": {"status": "completed", "delivered": now}}
                )

        except Exception as e:
            log.error(f"Failed to process reminder {reminder.get('_id')}: {e}")
            retry_count = reminder.get("retry_count", 0)
            if retry_count < 3:
                await self.db.update_one(
                    {"_id": reminder["_id"]},
                    {
                        "$set": {"retry_count": retry_count + 1},
                        "$inc": {"due": 300}  # Retry in 5 minutes
                    }
                )
            else:
                await self.db.update_one(
                    {"_id": reminder["_id"]},
                    {"$set": {"status": "failed", "error": str(e)[:200]}}
                )

    async def _process_reminder_batch(self, batch: list, now: datetime):
        """Process a batch of reminders"""
        for reminder in batch:
            try:
                await self._process_single_reminder(reminder, now)
            except Exception as e:
                log.error(f"Error processing reminder {reminder.get('_id')}: {e}")

    async def _clean_timezone_cache(self):
        """Clean timezone cache for inactive users"""
        active_users = set()
        async for reminder in self.db.find({"status": "active"}, {"user_id": 1}):
            active_users.add(reminder["user_id"])
        self.timezone_manager.clean_cache(active_users)

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
    # ║░░░░░░░░░░░░░░░░░░░ REMINDME_COMMAND ░░░░░░░░░░░░░░░░░░░░░░░║
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
            SEPARATORS = [" | ", " - ", " / ", " > ", " [", " — "]

            separator = None
            for sep in SEPARATORS:
                if sep in input_string:
                    separator = sep
                    break

            if not separator:
                return await ctx.send(
                    "# ⚠️ Missing separator!\n"
                    "Please split the time and reminder text with one of these:\n"
                    "`|` `-` `/` `>` `[` `—`\n\n"
                    "**Example:**\n"
                    "`!remind in 2 hours | take out the trash`"
                )

            time_part, reminder_text = input_string.split(separator, 1)
            reminder_text = reminder_text.strip()

            if not reminder_text:
                return await ctx.send("⚠️ Reminder text cannot be empty!")

            # Parse time with user's timezone
            try:
                user_tz = await self.timezone_manager.get_user_timezone(ctx.author.id)
                settings = {
                    'RELATIVE_BASE': datetime.now(user_tz),
                    'TIMEZONE': str(user_tz),
                    'TO_TIMEZONE': 'UTC',
                    'PREFER_DATES_FROM': 'future'
                }
                due = dateparser.parse(time_part, settings=settings)

                if not due:
                    raise ValueError("Could not parse time")

                # Ensure UTC timezone
                due = pytz.UTC.localize(due) if due.tzinfo is None else due.astimezone(pytz.UTC)

                # Validate future time
                if due <= datetime.now(pytz.UTC) + timedelta(seconds=10):  # 10 second buffer
                    current_time_str = await self.timezone_manager.format_time_with_timezone(
                        datetime.now(pytz.UTC), ctx.author.id
                    )
                    entered_time_str = await self.timezone_manager.format_time_with_timezone(
                        due, ctx.author.id
                    )
                    return await ctx.send(
                        f"### ⏳ **Time must be in the future!**\n"
                        f"You entered: `{entered_time_str}`\n"
                        f"Current time: `{current_time_str}`"
                    )
            except Exception as e:
                return await ctx.send(
                    "### ⚠️ Couldn't understand the time.\nTry formats like:\n"
                    "• `in 5 minutes`\n• `tomorrow at 3pm`\n• `next monday`\n\n"
                    f"Error: {str(e)[:100]}"
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
                    f"### ⏳ **Time must be in the future!**\n"
                    f"You entered: `{entered_time_str}`\n"
                    f"Current time: `{current_time_str}`"
                )

            # Show recurring options
            reminder_data = {
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "guild_id": ctx.guild.id if ctx.guild else None,  # Add this line
                "text": reminder_text,
                "due": due
            }

            time_str = await self.timezone_manager.format_time_with_timezone(due, ctx.author.id)

            embed = discord.Embed(
                description=(
                    f"# ⏰ **Set reminder for:**\n"
                    f"**When:** {time_str}\n"
                    f"**Reminder:** {reminder_text}\n\n"
                    f"Your reminder is almost ready"
                ),
                color=discord.Color.blue()
            )
            # Set thumbnail
            embed.set_thumbnail(url=logo)
            embed.set_footer(text="Choose One-time or Recurring")

            view = RecurringView(self, ctx.author.id, reminder_data)
            msg = await ctx.send(embed=embed, view=view)
            await msg.delete(delay=60)  # delete embed after a minute

        except Exception as e:
            await ctx.send(
                f"❌ **Error setting reminder:** {str(e)[:100]}\n\n"
                "**Proper Usage Examples:**\n"
                "• `!remind in 2 hours | take out the trash`\n"
                "• `!remind tomorrow at 3pm - buy groceries`", delete_after=15
            )

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░░░░░ REMINDERS ░░░░░░░░░░░░░░░░░░░░░░░░░░║
    # ╚════════════════════════════════════════════════════════════╝
    @commands.command(aliases=["myreminders", "mr"])
    async def reminders(self, ctx):
        """List your active reminders in a paginated embed"""
        try:
            # Fetch reminders from database
            reminders = await self.db.find(
                {"user_id": ctx.author.id, "status": "active"}
            ).sort("due", 1).to_list(None)

            if not reminders:
                embed = discord.Embed(
                    description="## ⏰ You have no active reminders!",
                    color=0x00ff00
                )
                # Set thumbnail
                embed.set_thumbnail(url=logo)
                return await ctx.send(embed=embed)

            # Create embeds data for paginator
            embeds_data = []
            for rem in reminders:
                embeds_data.append({
                    "_id": rem["_id"],
                    "text": rem["text"],
                    "due": rem["due"],
                    "recurring": rem.get("recurring")
                })

            # Create actual embeds
            embeds = []
            for idx, rem_data in enumerate(embeds_data, 1):
                time_str = await self.timezone_manager.format_time_with_timezone(
                    rem_data["due"], ctx.author.id
                )

                embed = discord.Embed(
                    description=f"### 📝 Saved Reminder:\n# {rem_data['text']}",
                    color=discord.Color(0xd0d88f),
                    timestamp=rem_data["due"]
                )

                embed.set_author(
                    name=f"⏰ Reminder #{idx} for {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )

                # Set thumbnail
                embed.set_thumbnail(url=logo)

                embed.add_field(
                    name="📆 When:",
                    value=f"```cs\n{time_str}\n```",
                    inline=False
                )

                if rem_data.get("recurring"):
                    embed.add_field(
                        name="🔄 Recurring:",
                        value=f"`{rem_data['recurring'].title()}`",
                        inline=True
                    )

                embed.set_footer(text=f"ID: {rem_data['_id']}")
                embeds.append(embed)

            # Send paginated view
            message = await ctx.send(embed=embeds[0])
            paginator = ReminderPaginator(embeds, ctx.author.id, message, self)
            await message.edit(view=paginator)
            await message.delete(delay=60)  # delete embed after a minute

        except Exception as e:
            log.error(f"Error in reminders command: {e}")
            error_embed = discord.Embed(
                title="❌ Error fetching reminders",
                description=f"```{str(e)[:1000]}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    """Discord.py Setup function"""
    await bot.add_cog(Reminder(bot))