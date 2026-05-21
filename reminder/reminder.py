# reminder.py
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import dateparser
import pymongo
import pytz
from dateutil.relativedelta import relativedelta

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from core import checks
from core.models import PermissionLevel

from .remindertimezone import ReminderTimezone, TimezoneConverter
from .remindercore import ReminderPaginator, SnoozeView, RecurringView, DualDeliveryView

log = logging.getLogger("Modmail")
__version__ = "4.01"
logo = "https://i.imgur.com/677JpTl.png"

# BUG FIX (🐛 Rigid Separator Flanking Space Rules):
# The old code used a plain list of strings that required exact surrounding spaces,
# so "2h|trash" was rejected. A compiled regex handles optional whitespace on both
# sides of any supported separator character.
SEPARATOR_PATTERN = re.compile(r'\s*(?:\||-|/|>|\[|—)\s*')


class Reminder(commands.Cog):
    """
    Reminder plugin with timezone support
    - `!remind [time] [sep] | [text]` -> Starts the multi-step `RecurringView` registration wizard.
    - `!reminders` (Aliases: `myreminders`, `mr`) -> Displays the stateful, multi-page `ReminderPaginator` active management panel.
    - `!mytimezone [string]` (Aliases: `settimezone`, `settz`) -> Validates and saves profile time configurations.
    - `!mytime` -> Returns current system time mapped directly to saved user location tables.
    - `!clearreminders` (Aliases: `clearcompleted`, `dropreminders`) -> Bulk purges historical completed log records.
    - **Raw Reaction Watcher:** `on_raw_reaction_add` scans for the `☑️` emoji on messages sent by the bot titled `"⏰ Reminder Alert!"` to allow recipients to dismiss them.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.timezone_manager = ReminderTimezone(self.db)
        self.reminder_loop.start()
        self.bot.loop.create_task(self._create_indexes())
        self.checkmark_emoji = "☑️"

    async def _create_indexes(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.db.create_index(
                    [("user_id", 1), ("status", 1)],
                    name="user_status_index", sparse=True
                )
                await self.db.create_index(
                    [("due", 1), ("status", 1)],
                    name="due_status_index", sparse=True
                )
                return
            except pymongo.errors.OperationFailure as e:
                if attempt == max_retries - 1:
                    log.error(f"Failed to create indexes after {max_retries} attempts: {e}")
                    raise
                await asyncio.sleep(1)

    def cog_unload(self):
        self.reminder_loop.cancel()

    async def get_user_timezone(self, user_id: int):
        return await self.timezone_manager.get_user_timezone(user_id)

    # +------------------------------------------------------------+
    # |    Commands                                                |
    # +------------------------------------------------------------+

    @commands.command(name="mytimezone", aliases=["settimezone", "settz"])
    @commands.guild_only()
    async def set_timezone(self, ctx, *, timezone_str: str):
        """Set your timezone (`!mytimezone UTC+2`)"""
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            timezone = await self.timezone_manager.set_user_timezone(ctx.author.id, timezone_str)

            if not timezone:
                return await ctx.send(
                    "❌ **Invalid timezone format!**\n"
                    "Use `UTC±HH` format (e.g., `UTC+2`, `UTC-5`) or a named timezone (e.g., `America/New_York`)\n"
                    "Offset must be between UTC-12 and UTC+14",
                    delete_after=9
                )

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
            embed.set_thumbnail(url=logo)
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=60)

        except Exception as e:
            msg = await ctx.send(f"❌ Error setting timezone: {str(e)[:100]}")
            await msg.delete(delay=60)

    @commands.command(name="mytime")
    @commands.guild_only()
    async def show_current_time(self, ctx):
        """Show your current time based on your timezone setting"""
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            user_tz = await self.timezone_manager.get_user_timezone(ctx.author.id)
            current_time = await self.timezone_manager.format_time_with_timezone(
                datetime.now(pytz.UTC), ctx.author.id
            )
            tz_display = self.timezone_manager.get_timezone_display(user_tz)

            embed = discord.Embed(
                description=(
                    f"# {current_time}\n"
                    f"**Timezone:** `{tz_display}` set by {ctx.author.display_name}"
                ),
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=logo)
            embed.set_author(
                name=f"⏰ Your current time: {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=60)

        except Exception as e:
            msg = await ctx.send(f"❌ Error fetching time: {str(e)[:100]}")
            await msg.delete(delay=60)

    # +------------------------------------------------------------+
    # |    @ Background Loop                                       |
    # +------------------------------------------------------------+

    @tasks.loop(seconds=60.0)
    async def reminder_loop(self):
        """Check reminders every minute with batch processing"""
        try:
            await self.bot.wait_until_ready()
            now = datetime.now(pytz.UTC)
            async for batch in self._get_reminder_batches(now):
                await self._process_reminder_batch(batch, now)
            if now.minute == 0:
                await self._clean_timezone_cache()
        except Exception as e:
            log.error(f"Reminder loop error: {e}", exc_info=True)

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def _get_reminder_batches(self, now: datetime):
        """Yield batches of 50 reminders at a time"""
        query = {"due": {"$lte": now}, "status": "active"}
        # BUG FIX (🐛 Deadlock on MongoDB Driver Sorting Types): list-of-tuples
        cursor = self.db.find(query).sort([("due", 1)]).batch_size(50)

        while True:
            batch = await cursor.to_list(length=50)
            if not batch:
                break
            yield batch

    async def _process_single_reminder(self, reminder: dict, now: datetime):
        """Deliver a reminder to DM and originating channel with fallback"""
        try:
            user = self.bot.get_user(reminder["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(reminder["user_id"])
                except discord.NotFound:
                    await self.db.delete_many({"user_id": reminder["user_id"], "status": "active"})
                    return

            time_str = await self.timezone_manager.format_time_with_timezone(
                reminder["due"], reminder["user_id"]
            )

            def make_embed():
                embed = discord.Embed(
                    # BUG FIX (🐛 Mismatched Verification Matrix for Reaction Dismissals)
                    title="⏰ Reminder!",
                    description=f"# {reminder['text']}",
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
                embed.set_footer(text=f"React with {self.checkmark_emoji} to dismiss")
                return embed

            delivery_status = {
                "dm_success": False,
                "channel_success": False,
                "dm_error": None,
                "channel_error": None
            }

            # --- DM delivery ---
            try:
                # BUG FIX (🐛 Multi-View Instance Collision & State Fragmentation):
                # Each send site now gets its own independent View instance.
                dm_view = DualDeliveryView(self, reminder["_id"], reminder["user_id"])
                dm_message = await user.send(embed=make_embed(), view=dm_view)
                await dm_message.add_reaction(self.checkmark_emoji)
                dm_view.message = dm_message  # needed for on_timeout cleanup
                delivery_status["dm_success"] = True
            except discord.Forbidden:
                delivery_status["dm_error"] = "User disabled DMs"
            except Exception as e:
                delivery_status["dm_error"] = str(e)[:100]

            # --- Original channel delivery ---
            try:
                channel = self.bot.get_channel(reminder["channel_id"])
                if not channel:
                    channel = await self.bot.fetch_channel(reminder["channel_id"])

                ch_view = DualDeliveryView(self, reminder["_id"], reminder["user_id"])

                if isinstance(channel, (discord.DMChannel, discord.PartialMessageable)):
                    ch_msg = await channel.send(f"{user.mention}", embed=make_embed(), view=ch_view)
                    await ch_msg.add_reaction(self.checkmark_emoji)
                    ch_view.message = ch_msg
                else:
                    ch_msg = await channel.send(f"{user.mention}", embed=make_embed(), view=ch_view)
                    await ch_msg.add_reaction(self.checkmark_emoji)
                    ch_view.message = ch_msg
                    await ch_msg.delete(delay=60)

                delivery_status["channel_success"] = True
            except discord.Forbidden:
                delivery_status["channel_error"] = "Missing permissions in channel"
            except discord.NotFound:
                delivery_status["channel_error"] = "Channel not found"
            except Exception as e:
                delivery_status["channel_error"] = str(e)[:100]

            # --- Fallback to first available guild channel ---
            if not delivery_status["dm_success"] and not delivery_status["channel_success"]:
                guild = self.bot.get_guild(reminder.get("guild_id"))
                if guild:
                    try:
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                footer_parts = []
                                if delivery_status["dm_error"]:
                                    footer_parts.append(f"DM failed: {delivery_status['dm_error']}")
                                if delivery_status["channel_error"]:
                                    footer_parts.append(f"Original channel failed: {delivery_status['channel_error']}")
                                fb_embed = make_embed()
                                fb_embed.set_footer(text=" | ".join(footer_parts))
                                fb_view = DualDeliveryView(self, reminder["_id"], reminder["user_id"])
                                fb_msg = await ch.send(f"{user.mention}", embed=fb_embed, view=fb_view)
                                await fb_msg.add_reaction(self.checkmark_emoji)
                                fb_view.message = fb_msg
                                break
                    except Exception:
                        pass

            # --- Reschedule or mark completed ---
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
                        "$inc": {"due": 300}
                    }
                )
            else:
                await self.db.update_one(
                    {"_id": reminder["_id"]},
                    {"$set": {"status": "failed", "error": str(e)[:200]}}
                )

    async def _process_reminder_batch(self, batch: list, now: datetime):
        for reminder in batch:
            try:
                await self._process_single_reminder(reminder, now)
            except Exception as e:
                log.error(f"Error processing reminder {reminder.get('_id')}: {e}")

    async def _clean_timezone_cache(self):
        """Clean timezone cache for inactive users"""
        active_users = set()
        # BUG FIX (🐛 Dead Loop Execution on Uniterable Mongo Cursors)
        docs = await self.db.find({"status": "active"}, {"user_id": 1}).to_list(None)
        for reminder in docs:
            active_users.add(reminder["user_id"])
        self.timezone_manager.clean_cache(active_users)

    async def _reschedule_recurring(self, reminder: dict):
        """Reschedule recurring reminders maintaining original time-of-day"""
        try:
            frequency = reminder["recurring"]
            original_due = reminder["due"]

            user_tz = await self.timezone_manager.get_user_timezone(reminder["user_id"])
            user_time = original_due.astimezone(user_tz)

            original_hour = user_time.hour
            original_minute = user_time.minute

            if frequency == "daily":
                next_date = user_time + timedelta(days=1)
            elif frequency == "weekly":
                next_date = user_time + timedelta(weeks=1)
            elif frequency == "monthly":
                next_date = user_time + relativedelta(months=1)
            else:
                log.error(f"Unknown recurring frequency: {frequency}")
                return

            # BUG FIX (🐛 Pytz Localization Crash on Pre-Localized Dates)
            naive_next = datetime(
                next_date.year, next_date.month, next_date.day,
                original_hour, original_minute
            )
            next_user_time = user_tz.localize(naive_next)
            next_due = next_user_time.astimezone(pytz.UTC)

            await self.db.update_one(
                {"_id": reminder["_id"]},
                {
                    "$set": {"due": next_due, "status": "active"},
                    "$unset": {"retry_count": ""}
                }
            )

        except Exception as e:
            log.error(f"Failed to reschedule recurring reminder {reminder.get('_id')}: {e}")
            await self.db.update_one(
                {"_id": reminder["_id"]},
                {"$set": {"status": "failed", "error": "reschedule_failed"}}
            )

    # +------------------------------------------------------------+
    # |    !remind                                                 |
    # +------------------------------------------------------------+

    @commands.command(aliases=["remindme", "reminder"], description="Powered by PYTZ")
    @commands.guild_only()
    async def remind(self, ctx, *, input_string: str):
        """Set a reminder - Usage: `!remind [time] SEPARATOR [text]`

        Supported separators: **| - / > [ —**
        Examples:
        • `!remind in 2 hours | take out the trash`
        • `!remind tomorrow at 3pm - buy groceries`
        • `!remind in 3 days / finish the report`
        """
        try:
            # BUG FIX (🐛 Rigid Separator Flanking Space Rules): the separator character is optional.
            parts = SEPARATOR_PATTERN.split(input_string, maxsplit=1)
            if len(parts) < 2:
                return await ctx.send(
                    "# ⚠️ Missing separator!\n"
                    "Please split the time and reminder text with one of these:\n"
                    "`|` `-` `/` `>` `[` `—`\n\n"
                    "**Example:**\n"
                    "`!remind in 2 hours | take out the trash`",
                    delete_after=9
                )

            time_part, reminder_text = parts[0].strip(), parts[1].strip()

            if not reminder_text:
                return await ctx.send("⚠️ Reminder text cannot be empty!", delete_after=9)

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

                due = pytz.UTC.localize(due) if due.tzinfo is None else due.astimezone(pytz.UTC)

                if due <= datetime.now(pytz.UTC) + timedelta(seconds=10):
                    current_time_str = await self.timezone_manager.format_time_with_timezone(
                        datetime.now(pytz.UTC), ctx.author.id
                    )
                    entered_time_str = await self.timezone_manager.format_time_with_timezone(
                        due, ctx.author.id
                    )
                    return await ctx.send(
                        f"### ⏳ **Time must be in the future!**\n"
                        f"You entered: `{entered_time_str}`\n"
                        f"Current time: `{current_time_str}`",
                        delete_after=9
                    )
            except Exception as e:
                return await ctx.send(
                    f"### ⚠️ Couldn't understand the time.\nTry formats like:\n"
                    "• `in 5 minutes`\n• `tomorrow at 3pm`\n• `next monday`\n\n"
                    f"Error: {str(e)[:100]}",
                    delete_after=9
                )

            reminder_data = {
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "guild_id": ctx.guild.id,
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
            embed.set_thumbnail(url=logo)
            embed.set_footer(text="Choose One-time or Recurring")

            # BUG FIX (🐛 Dangling Views and Memory Leaks via Delayed Deletes)
            view = RecurringView(self, ctx.author.id, reminder_data)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg  # allow on_timeout to edit it

        except Exception as e:
            await ctx.send(
                f"❌ **Error setting reminder:** {str(e)[:100]}\n\n"
                "**Proper Usage Examples:**\n"
                "• `!remind in 2 hours | take out the trash`\n"
                "• `!remind tomorrow at 3pm - buy groceries`",
                delete_after=15
            )

        finally:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

    # +------------------------------------------------------------+
    # |    !reminders                                              |
    # +------------------------------------------------------------+

    @commands.command(aliases=["myreminders", "mr"])
    @commands.guild_only()
    async def reminders(self, ctx):
        """List your active reminders in a paginated embed"""
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            # BUG FIX (🐛 Deadlock on MongoDB Driver Sorting Types): to satisfy Motor's requirement.
            reminders = await self.db.find(
                {"user_id": ctx.author.id, "status": "active"}
            ).sort([("due", 1)]).to_list(None)

            if not reminders:
                embed = discord.Embed(
                    description="## ⏰ You have no active reminders!",
                    color=0x00FF00
                )
                embed.set_thumbnail(url=logo)
                return await ctx.send(embed=embed, delete_after=10)

            embeds = []
            reminder_dicts = []  # BUG FIX: raw data stored alongside embeds for paginator

            for idx, rem in enumerate(reminders, 1):
                time_str = await self.timezone_manager.format_time_with_timezone(
                    rem["due"], ctx.author.id
                )

                embed = discord.Embed(
                    description=f"### 📝 Saved Reminder:\n# {rem['text']}",
                    color=discord.Color(0xD0D88F),
                    timestamp=rem["due"]
                )
                embed.set_author(
                    name=f"⏰ Reminder #{idx} for {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                embed.set_thumbnail(url=logo)
                embed.add_field(name="📆 When:", value=f"```cs\n{time_str}\n```", inline=False)

                if rem.get("recurring"):
                    embed.add_field(
                        name="🔄 Recurring:",
                        value=f"`{rem['recurring'].title()}`",
                        inline=True
                    )

                embed.set_footer(text=f"ID: {rem['_id']}")
                embeds.append(embed)
                reminder_dicts.append(rem)

            # BUG FIX (🐛 Fragile Scraper Architecture): ReminderPaginator receives raw reminder dicts
            message = await ctx.send(embed=embeds[0])
            paginator = ReminderPaginator(embeds, reminder_dicts, ctx.author.id, message, self)
            await message.edit(view=paginator)

        except Exception as e:
            log.error(f"Error in reminders command: {e}")
            error_embed = discord.Embed(
                title="❌ Error fetching reminders",
                description=f"```{str(e)[:1000]}```",
                color=0xFF0000
            )
            msg = await ctx.send(embed=error_embed)
            await msg.delete(delay=60)

    # +------------------------------------------------------------+
    # |    !clearreminders                                         |
    # +------------------------------------------------------------+

    @commands.command(aliases=["clearcompleted", "dropreminders"])
    @commands.guild_only()
    async def clearreminders(self, ctx):
        """Delete all your completed reminders from the database"""
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            count = await self.db.count_documents({
                "user_id": ctx.author.id,
                "status": "completed"
            })

            if count == 0:
                embed = discord.Embed(
                    description="## ✅ No completed reminders to clear!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=logo)
                msg = await ctx.send(embed=embed)
                await msg.delete(delay=10)
                return

            result = await self.db.delete_many({
                "user_id": ctx.author.id,
                "status": "completed"
            })

            embed = discord.Embed(
                description=(
                    f"## 🗑️ **Cleared {result.deleted_count} completed "
                    f"reminder{'s' if result.deleted_count != 1 else ''}!**\n"
                    f"Your database has been cleaned."
                ),
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=logo)
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=260)

        except Exception as e:
            log.error(f"Error clearing completed reminders: {e}")
            error_embed = discord.Embed(
                title="❌ Error clearing reminders",
                description=f"```{str(e)[:1000]}```",
                color=discord.Color.red()
            )
            msg = await ctx.send(embed=error_embed)
            await msg.delete(delay=60)

    # +------------------------------------------------------------+
    # |    !remindadm GROUP                                        |
    # +------------------------------------------------------------+

    @commands.group(name="remindadm", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remindadm(self, ctx: commands.Context):
        """Administrative command group for managing the Reminder plugin system."""
        await ctx.send_help(ctx.command)

    # +------------------------------------------------------------+
    # |    !remindadm view                                         |
    # +------------------------------------------------------------+

    @remindadm.command(name="view")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remindadm_view(self, ctx: commands.Context, target: discord.User):
        """
        View and manage a specific user's active reminders.
        Usage: !remindadm view @member OR !remindadm view 123456789012345
        """
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            raw_reminders = await self.db.find(
                {"user_id": target.id, "status": "active"}
            ).sort([("due", 1)]).to_list(length=100)

            if not raw_reminders:
                embed = discord.Embed(
                    title="🛡️ Admin Control Panel",
                    description=f"### **Clean Slate!**\nUser {target.mention} does not have any pending reminders scheduled.",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=logo)
                await ctx.send(embed=embed, delete_after=15.0)
                return

            embeds = []
            for idx, rem in enumerate(raw_reminders, 1):
                time_str = await self.timezone_manager.format_time_with_timezone(
                    rem["due"], rem["user_id"]
                )
                embed = discord.Embed(
                    description=f"### 📝 Saved Reminder:\n# {rem['text']}",
                    color=discord.Color(0xD0D88F),
                    timestamp=rem["due"]
                )
                embed.set_author(
                    name=f"🛡️ Admin Managing: {target.display_name} — Reminder #{idx}",
                    icon_url=target.avatar.url if target.avatar else target.default_avatar.url
                )
                embed.set_thumbnail(url=logo)
                embed.add_field(name="📆 When:", value=f"```cs\n{time_str}\n```", inline=False)
                if rem.get("recurring"):
                    embed.add_field(
                        name="🔄 Recurring:",
                        value=f"`{rem['recurring'].title()}`",
                        inline=True
                    )
                embed.set_footer(text=f"ID: {rem['_id']}")
                embeds.append(embed)

            menu_msg = await ctx.send(embed=embeds[0])
            paginator = ReminderPaginator(embeds, raw_reminders, ctx.author.id, menu_msg, self)
            await menu_msg.edit(view=paginator)

        except Exception as e:
            log.error(f"Admin view command failed for user {target.id}: {e}")
            await ctx.send("❌ Admin Error: Unable to safely generate user reminder display panel.", delete_after=10.0)

    # +------------------------------------------------------------+
    # |    !remindadm purge                                        |
    # +------------------------------------------------------------+

    @remindadm.command(name="purge")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remindadm_purge(self, ctx: commands.Context, flag: Optional[str] = None):
        """
        Purge reminder records from the plugin database partition.
        Usage: !remindadm purge (Clears all reminder records)
        Usage: !remindadm purge --drop (Wipes ALL data including user timezones for a clean install)
        """
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            confirm_embed = discord.Embed(
                title="⚠️ Critical Database Purge Warning",
                description="Are you absolutely sure you want to perform this operation?\n"
                            "This action will permanently alter or erase stored data.",
                color=discord.Color.red()
            )

            if flag == "--drop":
                confirm_embed.description += "\n\n🔥 **CRITICAL:** You used `--drop`. This will completely flush **ALL** tables including user timezone configurations for a factory reset."
            else:
                confirm_embed.description += "\n\n🧹 This will delete **all** reminders (active, completed, and failed) across the entire bot partition."

            confirm_embed.set_footer(text="Type 'confirm' within 15 seconds to proceed. Anything else cancels.")
            prompt_msg = await ctx.send(embed=confirm_embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirm'

            try:
                await self.bot.wait_for('message', check=check, timeout=15.0)
            except asyncio.TimeoutError:
                await prompt_msg.edit(content="❌ **Purge Operation Aborted:** Confirmation timed out.", embed=None, view=None)
                return

            if flag == "--drop":
                await self.db.drop()
                await self._create_indexes()
                self.timezone_manager.user_timezones.clear()
                result_text = "💥 **Database Partition Completely Dropped and Re-Indexed!**\nAll reminders and user timezone configs have been wiped cleanly for a fresh install."
            else:
                result_active = await self.db.delete_many({"status": {"$in": ["active", "completed", "failed"]}})
                result_fallback = await self.db.delete_many({"_id": {"$regex": "^(?!(timezone_)).*$"}})
                total_deleted = result_active.deleted_count + result_fallback.deleted_count
                result_text = f"🗑️ **Reminders Purge Complete!**\nSuccessfully deleted **{total_deleted}** total reminder logs across the entire partition. User timezones remain preserved."

            success_embed = discord.Embed(
                title="🛡️ Admin System Maintenance",
                description=result_text,
                color=discord.Color.green()
            )
            success_embed.set_thumbnail(url=logo)
            await prompt_msg.edit(embed=success_embed)

        except Exception as e:
            log.error(f"Critical administrative purge execution routine failed: {e}")
            await ctx.send("❌ Admin Error: Database execution transaction failed abruptly.", delete_after=15.0)

    # +------------------------------------------------------------+
    # |    @ Reaction listener                                     |
    # +------------------------------------------------------------+

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle checkmark reactions to dismiss delivered reminders"""
        if payload.user_id == self.bot.user.id:
            return
        if str(payload.emoji) != self.checkmark_emoji:
            return

        try:
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(payload.channel_id)
                except discord.NotFound:
                    return

            if isinstance(channel, discord.Thread):
                return

            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return

            if not (
                message.author.id == self.bot.user.id
                and message.embeds
                and message.embeds[0].title == "⏰ Reminder!"
            ):
                return

            user_can_dismiss = False

            if message.content and f"<@{payload.user_id}>" in message.content:
                user_can_dismiss = True
            elif isinstance(channel, discord.DMChannel):
                # BUG FIX (🐛 Fragile Reaction DM User Checks)
                if payload.user_id != self.bot.user.id:
                    user_can_dismiss = True

            if user_can_dismiss:
                await message.delete()

        except discord.Forbidden:
            pass
        except Exception as e:
            log.error(f"Error processing reaction in reminder: {e}")


async def setup(bot):
    """Discord.py Setup function"""
    await bot.add_cog(Reminder(bot))
