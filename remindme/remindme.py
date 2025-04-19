"""
v2.00
!plugin update WebKide/modmail-plugins/remindme@master
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

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import re
import logging
import asyncio

import discord
from discord.ext import commands, tasks
from discord import utils
from bson import ObjectId

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime
from .util.formatter import ReminderPaginator

UTC = timezone.utc
log = logging.getLogger(__name__)

class RemindMe(commands.Cog):
    """Improved Reminder Plugin with editing and recurring reminders"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.reminder_task.start()
        self.editing_users = {}  # {user_id: reminder_id}
    
    async def cog_load(self):
        await self.db.create_index([("due", 1)])
        await self.db.create_index([("user_id", 1)])
    
    async def cog_unload(self):
        self.reminder_task.cancel()

    def parse_with_separator(self, text: str) -> tuple:
        """Parse reminder text using separators with word support"""
        text_lower = text.lower()
        word_separators = ['in', 'at', 'on', 'for']
        
        # Replace time words with separator
        for word in word_separators:
            if word in text_lower:
                idx = text_lower.find(word) + len(word)
                return text[:idx].strip(), text[idx:].strip()
        
        # Traditional separators
        separators = ['<', '-', '|', '>', ':', '—']
        for sep in separators:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
        
        # Fallback to splitting at first time-like pattern
        time_pattern = r'\d+:\d+|\d+[hmsdwy]'
        match = re.search(time_pattern, text)
        if match:
            idx = match.start()
            return text[:idx].strip(), text[idx:].strip()
        
        return None, text

    @commands.command(name='remind', aliases=['remindme', 'rm'], no_pm=True)
    async def remind(self, ctx: commands.Context, *, text: str):
        """Create a reminder using separators between When and What

        - hyphen           -
        - bar                   |
        - colon               :
        - em dash        —
        - lower than    <
        - greater than >
        
        Examples:
        !remind May 20: camping trip
        !remind 20 May - birthday party
        !remind in 2 hours | remember the staff meeting
        """
        # Parse input
        date_part, reminder_text = self.parse_with_separator(text)
        
        if not reminder_text:
            return await ctx.send(embed=discord.Embed(
                title="Invalid format",
                description=f'Please include both time and reminder text.\nExample: `{ctx.prefix}remind in 2 hours buy milk`',
                color=self.bot.error_color
            ))
        
        dt = self.parse_natural_date(date_part)
        
        if dt is None:
            try:
                timeconverter = UserFriendlyTime()
                converted = await timeconverter.convert(ctx=ctx, argument=date_part, now=datetime.now(UTC))
                dt = converted.dt
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
            except commands.BadArgument as e:
                embed = discord.Embed(
                    title="Invalid time format",
                    description=str(e),
                    color=self.bot.error_color
                )
                return await ctx.send(embed=embed)
        
        if dt <= datetime.now(UTC):
            embed = discord.Embed(
                title="Invalid time",
                description="Reminder time must be in the future",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        reminder = {
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,  # Remember channel for context
            "text": reminder_text,
            "due": dt,
            "created_at": datetime.now(UTC)
        }
        
        result = await self.db.insert_one(reminder)
        reminder_id = str(result.inserted_id)
        
        embed = discord.Embed(
            title='✅ Reminder Created',
            description=f'**When:** {utils.format_dt(dt, "f")} ({utils.format_dt(dt, "R")})\n'
                       f'**What:** {reminder_text}',
            color=discord.Color.green()
        )
        embed.set_footer(text=f'ID: {reminder_id}')
        
        # Add delete button
        view = View(timeout=60)
        delete_button = Button(emoji="🗑️", style=discord.ButtonStyle.red)
        
        async def delete_callback(interaction):
            if interaction.user.id != ctx.author.id and not interaction.channel.permissions_for(interaction.user).administrator:
                await interaction.response.send_message("You don't have permission to delete this reminder.", ephemeral=True)
                return
                
            await self.db.delete_one({"_id": ObjectId(reminder_id)})
            embed.title = '🗑️ Reminder Deleted'
            embed.color = discord.Color.red()
            for item in view.children:
                item.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
        
        delete_button.callback = delete_callback
        view.add_item(delete_button)
        
        await ctx.send(embed=embed, view=view)

    @commands.command(name='delreminder', aliases=['forgetreminder'], no_pm=True)
    async def delreminder(self, ctx: commands.Context, reminder_id: str):
        """Delete one of your reminders"""
        try:
            reminder_id = ObjectId(reminder_id)
        except:
            embed = discord.Embed(
                title='Invalid Reminder ID',
                description='The reminder ID provided is not valid.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        result = await self.db.delete_one({"_id": reminder_id, "user_id": ctx.author.id})
        
        if result.deleted_count == 0:
            embed = discord.Embed(
                title='Reminder not found',
                description='No reminder with that ID was found or you don\'t have permission to delete it.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        embed = discord.Embed(
            title='✅ Reminder deleted',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
            
    @commands.command(name='reminders', aliases=['listreminders','lr'], no_pm=True)
    async def reminders(self, ctx: commands.Context):
        """List your active reminders"""
        reminders = await self.db.find({"user_id": ctx.author.id}).sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description='You don\'t have any active reminders!',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        embeds = []
        
        for reminder in reminders:
            truncated = (reminder["text"][:100] + '...') if len(reminder["text"]) > 100 else reminder["text"]
            embed = discord.Embed(
                title=f"⏰ Reminder for {utils.format_dt(reminder['due'], 'f')}",
                description=truncated,
                color=self.bot.main_color
            )
            embed.add_field(
                name="Details",
                value=f"Created: {utils.format_dt(reminder['created_at'], 'R')}\n"
                      f"Channel: <#{reminder.get('channel_id', 'DM')}>",
                inline=False
            )
            embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
            embeds.append(embed)
        
        if len(embeds) == 1:
            # Single reminder - show with delete button
            view = ReminderPaginator(embeds, self.db, is_admin=True if ctx.command.name == "admin_all_reminders" else False)
            view.current_page = 0
            view.timeout = 90  # 90-second timeout
            view.update_buttons()
            message = await ctx.send(embed=embeds[0], view=view)
            view.message = message
            # Start auto-delete timer
            asyncio.create_task(self.auto_delete_message(message))
        else:
            # Multiple reminders - paginate
            paginator = ReminderPaginator(self.bot, embeds, self.db, is_admin=True)
            message = await ctx.send(embed=embeds[0], view=paginator)
            paginator.message = message
            # Start auto-delete timer
            asyncio.create_task(self.auto_delete_message(message))

    @tasks.loop(seconds=30)
    async def reminder_task(self):
        """Check and send due reminders"""
        await self.bot.wait_until_ready()
        now = datetime.now(UTC)
        
        reminders = await self.db.find({"due": {"$lte": now}}).to_list(None)
        log.debug(f"Processing {len(reminders)} due reminders")
        
        for reminder in reminders:
            success = False
            try:
                # Try channel message
                if reminder.get("channel_id"):
                    channel = self.bot.get_channel(reminder["channel_id"])
                    if channel and not isinstance(channel, discord.Thread):
                        try:
                            msg = await channel.send(
                                f'<@{reminder["user_id"]}>',
                                embed=self.create_reminder_embed(reminder, is_dm=False)
                            )
                            await msg.add_reaction('🔁')  # Repeat button
                            await msg.add_reaction('❎')  # Close button
                            success = True
                        except discord.HTTPException as e:
                            log.warning(f"Failed to send channel reminder: {e}")

                # Try DM
                try:
                    user = await self.bot.get_or_fetch_user(reminder["user_id"])
                    if user:
                        dm_msg = await user.send(embed=self.create_reminder_embed(reminder, is_dm=True))
                        await dm_msg.add_reaction('🔁')
                        await dm_msg.add_reaction('🗑️')
                        success = True
                except discord.Forbidden:
                    log.debug(f"User {reminder['user_id']} has DMs disabled")
                except Exception as e:
                    log.error(f"Failed to send DM reminder: {e}")

                # Only delete if successfully delivered
                if success:
                    await self.db.delete_one({"_id": reminder["_id"]})
                else:
                    log.warning(f"Failed to deliver reminder {reminder['_id']}, keeping in database")

            except Exception as e:
                log.error(f"Error processing reminder {reminder.get('_id')}: {e}")

    def create_reminder_embed(self, reminder: dict, is_dm: bool) -> discord.Embed:
        """Create consistent reminder embed"""
        embed = discord.Embed(
            title=f"⏰ {'Reminder' if not is_dm else 'Reminder (DM)'}",
            description=f"```css\n{reminder['text'].capitalize()}\n```",
            color=self.bot.main_color
        )
        embed.add_field(
            name="Created",
            value=f"{utils.format_dt(reminder.get('created_at', datetime.now(UTC)), 'f')} "
                  f"({utils.format_dt(reminder.get('created_at', datetime.now(UTC)), 'R')})",
            inline=False
        )
        if reminder.get("channel_id") and not is_dm:
            embed.add_field(name="Channel", value=f"<#{reminder['channel_id']}>", inline=False)
        embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
        return embed


    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def reminders_admin(self, ctx: commands.Context):
        """Admin reminder management"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all", no_pm=True)
    @commands.has_permissions(administrator=True)
    async def admin_all_reminders(self, ctx: commands.Context):
        """View all active reminders (paginated with delete options)"""
        reminders = await self.db.find().sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        embeds = []
        for reminder in reminders:
            # Skip invalid reminders missing required fields
            if "user_id" not in reminder:
                continue
                
            try:
                user = await self.bot.get_or_fetch_user(reminder["user_id"])
                member = ctx.guild.get_member(user.id)  # Get member object for display name
                name = member.display_name if member else user.name
                avatar = user.avatar.url if user.avatar else None
            except:
                name = f"Unknown User ({reminder['user_id']})"
                avatar = None
            
            # Skip reminders missing required fields
            if "due" not in reminder or "text" not in reminder:
                continue
                
            embed = discord.Embed(
                title=f"Reminder for {name}",
                description=f"**Due:** {utils.format_dt(reminder['due'], 'f')}\n"
                           f"**Content:** {reminder['text'][:200]}",
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
            
            embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
            embeds.append(embed)
        
        if not embeds:
            embed = discord.Embed(
                title='No valid reminders found',
                description='All reminders in database were invalid',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        if len(embeds) == 1:
            # Single reminder - show with delete button
            view = ReminderPaginator(embeds, self.db, is_admin=True if ctx.command.name == "admin_all_reminders" else False)
            view.current_page = 0
            view.timeout = 90  # 90-second timeout
            view.update_buttons()
            message = await ctx.send(embed=embeds[0], view=view)
            view.message = message
            # Start auto-delete timer
            asyncio.create_task(self.auto_delete_message(message))
        else:
            # Multiple reminders - paginate
            paginator = ReminderPaginator(self.bot, embeds, self.db, is_admin=True)
            message = await ctx.send(embed=embeds[0], view=paginator)
            paginator.message = message
            # Start auto-delete timer
            asyncio.create_task(self.auto_delete_message(message))

    @reminders_admin.command(name="cleanup", no_pm=True)
    @commands.has_permissions(administrator=True)
    async def cleanup_reminders(self, ctx: commands.Context):
        """Clean up invalid reminders"""
        # Delete reminders missing required fields
        result = await self.db.delete_many({
            "$or": [
                {"user_id": {"$exists": False}},
                {"due": {"$exists": False}},
                {"text": {"$exists": False}}
            ]
        })
        
        embed = discord.Embed(
            title="Database Cleanup",
            description=f"Removed {result.deleted_count} invalid reminders",
            color=self.bot.main_color
        )
        await ctx.send(embed=embed)
        

async def setup(bot):
    await bot.add_cog(RemindMe(bot))
    
