"""
!plugin update WebKide/modmail-plugins/remindmepro@master
MIT License
Copyright (c) 2020-2025 WebKide [d.id @323578534763298816]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
import pytz
from bson import ObjectId
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from discord.ext import commands, tasks
from discord import utils
from discord.ui import Button, View

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime

UTC = timezone.utc
log = logging.getLogger(__name__)

class ReminderPaginator(View):
    """Custom paginator with enhanced controls"""
    def __init__(self, bot, embeds, db, user_id=None, is_admin=False):
        super().__init__(timeout=120)
        self.bot = bot
        self.embeds = embeds
        self.current_page = 0
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
        self.message = None
        self.update_buttons()

    async def on_timeout(self):
        try:
            await self.message.delete()
        except:
            pass

    def update_buttons(self):
        self.clear_items()
        
        # Always show page navigation if multiple pages
        if len(self.embeds) > 1:
            prev_button = Button(emoji="⬅️", style=discord.ButtonStyle.blurple, disabled=self.current_page == 0)
            prev_button.callback = self.previous_page
            self.add_item(prev_button)
            
            next_button = Button(emoji="➡️", style=discord.ButtonStyle.blurple, 
                               disabled=self.current_page == len(self.embeds) - 1)
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        # Edit button (owner only)
        if self.user_id is not None:
            edit_button = Button(emoji="✏️", style=discord.ButtonStyle.grey)
            edit_button.callback = self.edit_reminder
            self.add_item(edit_button)
        
        # Delete button (owner or admin)
        if self.user_id is not None or self.is_admin:
            delete_button = Button(emoji="🗑️", style=discord.ButtonStyle.red)
            delete_button.callback = self.delete_reminder
            self.add_item(delete_button)
        
        # Snooze and recurring buttons only for active reminders
        if hasattr(self, 'is_active_reminder') and self.is_active_reminder:
            snooze_button = Button(emoji="⏳", style=discord.ButtonStyle.green)
            snooze_button.callback = self.snooze_reminder
            self.add_item(snooze_button)
            
            daily_button = Button(emoji="🔁", style=discord.ButtonStyle.green)
            daily_button.callback = self.set_daily
            self.add_item(daily_button)
            
            weekly_button = Button(emoji="📆", style=discord.ButtonStyle.green)
            weekly_button.callback = self.set_weekly
            self.add_item(weekly_button)
        
        # Always show close button
        close_button = Button(emoji="❎", style=discord.ButtonStyle.grey)
        close_button.callback = self.close_message
        self.add_item(close_button)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()

    async def close_message(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.manage_messages:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You don't have permission to close this.", ephemeral=True)

    async def get_current_reminder(self):
        embed = self.embeds[self.current_page]
        if not embed.footer or not embed.footer.text.startswith('Reminder ID: '):
            return None
            
        reminder_id = embed.footer.text[13:]
        return await self.db.find_one({"_id": ObjectId(reminder_id)})

    async def delete_reminder(self, interaction: discord.Interaction):
        reminder = await self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder.", ephemeral=True)
            return
            
        if not self.is_admin and interaction.user.id != reminder["user_id"]:
            await interaction.response.send_message("You don't have permission to delete this reminder.", ephemeral=True)
            return
            
        await self.db.delete_one({"_id": reminder["_id"]})
        embed = self.embeds[self.current_page]
        embed.title = '🗑️ Reminder Deleted'
        embed.color = discord.Color.red()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def edit_reminder(self, interaction: discord.Interaction):
        reminder = await self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder.", ephemeral=True)
            return
            
        if interaction.user.id != reminder["user_id"]:
            await interaction.response.send_message("You can only edit your own reminders.", ephemeral=True)
            return
            
        modal = EditReminderModal(reminder)
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.new_time:
            try:
                new_dt = parse(modal.new_time, fuzzy=True)
                if new_dt.tzinfo is None:
                    new_dt = new_dt.replace(tzinfo=UTC)
                    
                await self.db.update_one(
                    {"_id": reminder["_id"]},
                    {"$set": {"due": new_dt}}
                )
                
                embed = self.embeds[self.current_page]
                embed.description = f"**New Time:** {utils.format_dt(new_dt, 'f')}\n" + \
                                  "\n".join(embed.description.split('\n')[1:])
                await interaction.followup.edit_message(embed=embed, view=self)
            except Exception as e:
                await interaction.followup.send(f"Error updating time: {str(e)}", ephemeral=True)

    async def snooze_reminder(self, interaction: discord.Interaction):
        reminder = await self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder.", ephemeral=True)
            return
            
        if interaction.user.id != reminder["user_id"] and not self.is_admin:
            await interaction.response.send_message("You can only snooze your own reminders.", ephemeral=True)
            return
            
        new_due = datetime.now(UTC) + timedelta(minutes=10)
        await self.db.update_one(
            {"_id": reminder["_id"]},
            {"$set": {"due": new_due}}
        )
        
        embed = self.embeds[self.current_page]
        embed.description = f"**Snoozed Until:** {utils.format_dt(new_due, 'f')}\n" + \
                          "\n".join(embed.description.split('\n')[1:])
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_daily(self, interaction: discord.Interaction):
        await self.set_recurring(interaction, "daily")

    async def set_weekly(self, interaction: discord.Interaction):
        await self.set_recurring(interaction, "weekly")

    async def set_recurring(self, interaction: discord.Interaction, frequency: str):
        reminder = await self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder.", ephemeral=True)
            return
            
        if interaction.user.id != reminder["user_id"]:
            await interaction.response.send_message("You can only modify your own reminders.", ephemeral=True)
            return
            
        await self.db.update_one(
            {"_id": reminder["_id"]},
            {"$set": {"recurring": frequency}}
        )
        
        embed = self.embeds[self.current_page]
        embed.add_field(name="Recurring", value=frequency.capitalize(), inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class EditReminderModal(discord.ui.Modal):
    def __init__(self, reminder):
        super().__init__(title="Edit Reminder")
        self.reminder = reminder
        self.new_time = None
        
        self.add_item(discord.ui.InputText(
            label="New Date/Time",
            placeholder="e.g. 'tomorrow at 3pm' or 'April 20'",
            value=utils.format_dt(reminder["due"], "f")
        ))
        
    async def callback(self, interaction: discord.Interaction):
        self.new_time = self.children[0].value
        await interaction.response.defer()

# ======================================================
#
#
#
#               REMIND ME PRO CLASS
#
#
#
# ======================================================
class RemindMePro(commands.Cog):
    """Advanced Reminder System with Timezone Support"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.user_timezones = {}
        self.reminder_task.start()

    async def cog_load(self):
        await self.db.create_index("due")
        await self.db.create_index("user_id")
        await self.load_timezones()

    async def cog_unload(self):
        self.reminder_task.cancel()

    async def load_timezones(self):
        async for user in self.db.find({"timezone": {"$exists": True}}):
            self.user_timezones[user["user_id"]] = user["timezone"]

    async def get_user_timezone(self, user_id):
        return pytz.timezone(self.user_timezones.get(user_id, "UTC"))

    async def check_dm_status(self, user):
        try:
            await user.send("Testing DM access", delete_after=23)
            return "✅ Enabled"
        except discord.Forbidden:
            return "❎ Disabled"

    # ======================================================
    #
    #
    #
    #               TIMEZONE GROUP COMMANDS
    #
    #
    #
    # ======================================================
    @commands.group(name="timezone", aliases=["tz"], invoke_without_command=True)
    async def timezone(self, ctx):
        """Manage your timezone settings"""
        await ctx.send_help(ctx.command)

    @timezone.command(name="set", no_pm=True)
    async def set_timezone(self, ctx, timezone: str):
        """Set your timezone (e.g. EST, PST, UTC+3)"""
        try:
            # Validate timezone
            tz = pytz.timezone(timezone)
            self.user_timezones[ctx.author.id] = timezone
            await self.db.update_one(
                {"user_id": ctx.author.id},
                {"$set": {"timezone": timezone}},
                upsert=True
            )
            await ctx.send(f"Your timezone has been set to {timezone}")
        except pytz.UnknownTimeZoneError:
            await ctx.send("Unknown timezone. Please use formats like EST, PST, or UTC+3")

    @timezone.command(name="view", no_pm=True)
    async def view_timezone(self, ctx):
        """View your current timezone setting"""
        tz = self.user_timezones.get(ctx.author.id, "UTC")
        await ctx.send(f"Your current timezone is set to: {tz}")

    # ======================================================
    #
    #
    #
    #               USER COMMANDS START HERE
    #
    #
    #
    # ======================================================
    @commands.command(name="remind", aliases=["remindme", "rm"], no_pm=True)
    async def remind(self, ctx, *, text: str):
        dm_status = await self.check_dm_status(ctx.author)
        
        try:
            # Get user's default timezone (if set)
            user_tz = await self.get_user_timezone(ctx.author.id)

            # Extract timezone abbreviations from text (e.g., "9pm EST")
            tz_pattern = r"\b([A-Z]{3,4})\b"
            if matches := re.findall(tz_pattern, text):
                try:
                    user_tz = pytz.timezone(matches[-1])  # Use the last matched timezone
                    text = re.sub(tz_pattern, "", text).strip()  # Remove timezone from text
                except pytz.UnknownTimeZoneError:
                    pass  # Fall back to user's default timezone

            # Parse with both fuzzy and tokens
            dt, tokens = parse(text, fuzzy_with_tokens=True, default=datetime.now(user_tz))
            
            # Extract reminder text from unused tokens
            reminder_text = " ".join(tokens).strip()
            
            # Convert to UTC if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            else:
                dt = dt.astimezone(UTC)
            
            # Handle relative times (e.g., "tomorrow", "next week")
            if dt <= datetime.now(UTC):
                if "tomorrow" in text.lower():
                    dt += timedelta(days=1)
                elif "next week" in text.lower():
                    dt += timedelta(weeks=1)

            # Handle pure duration formats
            if not reminder_text and "in " in text.lower():
                reminder_text = text.split("in ", 1)[-1].split(" ", 1)[-1]
                
            # Handle "noon"/"midnight" special cases
            if "noon" in text.lower() and not reminder_text:
                reminder_text = text.replace("noon", "").strip()
            elif "midnight" in text.lower() and not reminder_text:
                reminder_text = text.replace("midnight", "").strip()
                
        except Exception as e:
            embed = discord.Embed(
                title="Invalid Format",
                description=f"Could not parse time from your reminder.\nExample: `{ctx.prefix}remind May 20 at 3pm camping trip`",
                color=self.bot.error_color
            )
            embed.add_field(name="📩 Direct Messages", value=dm_status, inline=False)
            return await ctx.send(embed=embed, delete_after=260)
        
        if dt <= datetime.now(UTC):
            embed = discord.Embed(
                title="Invalid Time",
                description="Reminder time must be in the future",
                color=self.bot.error_color
            )
            embed.add_field(name="📩 Direct Messages", value=dm_status, inline=False)
            return await ctx.send(embed=embed, delete_after=260)
        
        reminder = {
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "text": reminder_text,
            "due": dt,
            "created_at": datetime.now(UTC),
            "recurring": None,
            "timezone": self.user_timezones.get(ctx.author.id, "UTC")
        }
        
        result = await self.db.insert_one(reminder)
        reminder_id = str(result.inserted_id)
        
        embed = discord.Embed(
            title='✅ Reminder Created',
            description=f'**When:**\n{utils.format_dt(dt, "f")} ({utils.format_dt(dt, "R")})\n'
                       f'**What:**\n```css\n{reminder_text}\n```',
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Reminder ID: {reminder_id}")
        embed.add_field(name="📩 Direct Messages", value=dm_status, inline=False)
        
        await ctx.send(embed=embed, delete_after=260)

    @commands.command(name="reminders", aliases=["listreminders", "lr"], no_pm=True)
    async def reminders(self, ctx):
        """List your active reminders"""
        reminders = await self.db.find({"user_id": ctx.author.id}).sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description="You don't have any active reminders!",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=260)
            
        embeds = []
        for idx, reminder in enumerate(reminders):
            truncated = (reminder["text"][:100] + '...') if len(reminder["text"]) > 100 else reminder["text"]
            embed = discord.Embed(
                title=f"⏰ Reminder {idx+1}/{len(reminders)}",
                description=f"**Due:**\n{utils.format_dt(reminder['due'], 'f')} ({utils.format_dt(reminder['due'], 'R')})\n"
                           f"**Content:**\n```css\n{truncated}\n```",
                color=self.bot.main_color
            )
            embed.add_field(
                name="Details",
                value=f"Created: {utils.format_dt(reminder['created_at'], 'R')}\n"
                      f"Channel: <#{reminder.get('channel_id', 'DM')}>",
                inline=False
            )
            if reminder.get("recurring"):
                embed.add_field(
                    name="Recurring",
                    value=f"every {reminder['recurring'].capitalize()}",
                    inline=False
                )
            embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
            embeds.append(embed)
        
        paginator = ReminderPaginator(self.bot, embeds, self.db, user_id=ctx.author.id)
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

    # ======================================================
    #
    #
    #
    #                     TASK LOOP
    #
    #
    #
    # ======================================================
    @tasks.loop(seconds=30)
    async def reminder_task(self):
        await self.bot.wait_until_ready()
        now = datetime.now(UTC)
        
        reminders = await self.db.find({"due": {"$lte": now}}).to_list(None)
        log.debug(f"Found {len(reminders)} due reminders at {now.isoformat()}")
        
        for reminder in reminders:
            try:
                # Handle recurring reminders first
                if reminder.get("recurring") == "daily":
                    new_due = reminder["due"] + timedelta(days=1)
                    await self.db.update_one(
                        {"_id": reminder["_id"]},
                        {"$set": {"due": new_due}}
                    )
                    continue
                elif reminder.get("recurring") == "weekly":
                    new_due = reminder["due"] + timedelta(weeks=1)
                    await self.db.update_one(
                        {"_id": reminder["_id"]},
                        {"$set": {"due": new_due}}
                    )
                    continue
                
                channel = None
                if reminder.get("channel_id"):
                    channel = self.bot.get_channel(reminder["channel_id"])
                
                # Format the reminder text
                formatted_text = reminder["text"][0].upper() + reminder["text"][1:]
                time_elapsed = utils.format_dt(reminder.get("created_at", datetime.now(UTC)), "R")

                embed = discord.Embed(
                    title='⏰ Reminder:',
                    description=f"```css\n{formatted_text}\n```",
                    color=self.bot.main_color
                )
                embed.add_field(
                    name="Created",
                    value=f"{utils.format_dt(reminder['created_at'], 'f')} ({time_elapsed})",
                    inline=False
                )
                # Add new field if reminder is recurring
                if reminder.get("recurring"):
                    embed.add_field(
                        name="Recurring:",
                        value=f"every {reminder['recurring']}",
                        inline=False
                    )
                if reminder.get("channel_id"):
                    embed.add_field(name="Channel", value=f"<#{reminder['channel_id']}>", inline=False)
                embed.set_footer(text=f'ID: {reminder["_id"]}')
                
                # Send to original channel if possible
                if channel:
                    try:
                        view = ReminderPaginator(self.bot, [embed], self.db, user_id=reminder["user_id"])
                        view.is_active_reminder = True  # <-- Add this line
                        msg = await channel.send(f'<@{reminder["user_id"]}>', embed=embed, view=view)
                    except discord.Forbidden:
                        log.warning(f"Missing permissions to send reminder in {reminder['channel_id']}")

                # Always try to send DM
                try:
                    user = await self.bot.get_or_fetch_user(reminder["user_id"])
                    if user:
                        view = ReminderPaginator(self.bot, [embed], self.db, user_id=reminder["user_id"])
                        view.is_active_reminder = True  # <-- Add this line
                        dm_msg = await user.send(embed=embed, view=view)
                except discord.Forbidden:
                    log.debug(f"Could not send DM to user {reminder['user_id']}")
                except Exception as e:
                    log.error(f"Failed to send DM for reminder {reminder['_id']}: {e}")
                
                # Delete non-recurring reminders
                if not reminder.get("recurring"):
                    await self.db.delete_one({"_id": reminder["_id"]})
                
            except Exception as e:
                log.error(f"Failed to process reminder {reminder['_id']}: {e}")
                continue

    # ======================================================
    #
    #
    #
    #               ADMIN COMMANDS START HERE
    #
    #
    #
    # ======================================================
    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def reminders_admin(self, ctx):
        """Admin reminder management"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all", no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def admin_all_reminders(self, ctx):
        """View all active reminders"""
        reminders = await self.db.find().sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed, delete_after=260)
        
        embeds = []
        for idx, reminder in enumerate(reminders):
            try:
                user = await self.bot.get_or_fetch_user(reminder["user_id"])
                username = user.name if user else f"Unknown User ({reminder['user_id']})"
                avatar = user.avatar.url if user and user.avatar else None
            except:
                username = f"Unknown User ({reminder['user_id']})"
                avatar = None
            
            truncated = (reminder["text"][:100] + '...') if len(reminder["text"]) > 100 else reminder["text"]
            embed = discord.Embed(
                title=f"⏰ Reminder {idx+1}/{len(reminders)} for {username}:",
                description=f"**Due:**\n{utils.format_dt(reminder['due'], 'f')}\n\n"
                           f"**Content:**\n```css\n{truncated}\n```",
                color=self.bot.main_color
            )
            
            if avatar:
                embed.set_thumbnail(url=avatar)
                
            embed.add_field(
                name="Info",
                value=f"User ID: `{reminder['user_id']}`\n"
                     f"Channel: <#{reminder.get('channel_id', 'DM')}>\n"
                     f"Created: {utils.format_dt(reminder.get('created_at', datetime.now(UTC)), 'R')}",
                inline=False
            )
            if reminder.get("recurring"):
                embed.add_field(
                    name="Recurring",
                    value=f"every {reminder['recurring'].capitalize()}",
                    inline=False
                )
            embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
            embeds.append(embed)
        
        paginator = ReminderPaginator(self.bot, embeds, self.db, is_admin=True)
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

async def setup(bot):
    await bot.add_cog(RemindMePro(bot))
