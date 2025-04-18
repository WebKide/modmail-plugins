"""
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
import os
import re
import logging

import discord
from discord.ext import commands, tasks
from discord import utils
from discord.ui import Button, View
from bson import ObjectId

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime
from core.paginator import EmbedPaginatorSession, MessagePaginatorSession

UTC = timezone.utc
log = logging.getLogger(__name__)

class ReminderPaginator(View):
    """Custom paginator with delete button for reminders"""
    def __init__(self, embeds, db, user_id=None, is_admin=False):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
        self.message = None
        
        # Update buttons on initialization
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.clear_items()
        
        # Previous button
        prev_button = Button(emoji="⬅️", style=discord.ButtonStyle.blurple, disabled=self.current_page == 0)
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Delete button (only if user is owner or admin)
        if self.user_id is not None or self.is_admin:
            delete_button = Button(emoji="🗑️", style=discord.ButtonStyle.red)
            delete_button.callback = self.delete_reminder
            self.add_item(delete_button)
        
        # Next button
        next_button = Button(emoji="➡️", style=discord.ButtonStyle.blurple, disabled=self.current_page == len(self.embeds) - 1)
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()
    
    async def delete_reminder(self, interaction: discord.Interaction):
        """Delete current reminder"""
        embed = self.embeds[self.current_page]
        if not embed.footer.text:
            await interaction.response.send_message("Could not find reminder ID.", ephemeral=True)
            return
            
        # Extract reminder ID from footer
        footer = embed.footer.text
        if not footer.startswith('Reminder ID: '):
            await interaction.response.send_message("Invalid reminder format.", ephemeral=True)
            return
            
        reminder_id = footer[13:]
        
        try:
            # Check permissions
            reminder = await self.db.find_one({"_id": ObjectId(reminder_id)})
            if not reminder:
                await interaction.response.send_message("Reminder not found.", ephemeral=True)
                return
                
            if not self.is_admin and (self.user_id is None or reminder["user_id"] != self.user_id):
                await interaction.response.send_message("You don't have permission to delete this reminder.", ephemeral=True)
                return
                
            # Delete the reminder
            await self.db.delete_one({"_id": ObjectId(reminder_id)})
            
            # Update the embed
            embed.title = '🗑️ Reminder Deleted'
            embed.color = discord.Color.red()
            self.update_buttons()
            
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            log.error(f"Error deleting reminder: {e}")
            await interaction.response.send_message("An error occurred while deleting the reminder.", ephemeral=True)
    
    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class RemindMe(commands.Cog):
    """Improved Reminder Plugin with separator parsing and admin tools"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.reminder_task.start()
    
    async def cog_load(self):
        await self.db.create_index("due")
        await self.db.create_index("user_id")
    
    async def cog_unload(self):
        self.reminder_task.cancel()

    def parse_with_separator(self, text: str) -> tuple:
        """Parse reminder text using separators"""
        separators = ['<', '-', '|', '>', ':', '—']
        for sep in separators:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
        return None, text  # Fallback to old behavior if no separator found

    def parse_natural_date(self, text: str) -> Optional[datetime]:
        """Parse natural language dates with improved handling"""
        now = datetime.now(UTC)
        text = text.lower().replace('of ', '').replace(' at ', ' ').replace(' on ', ' ')
        
        patterns = [
            # Month Day Year
            (r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(?: \d{4})?", "%b %d %Y"),
            # Day Month Year
            (r"\d{1,2} (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?: \d{4})?", "%d %b %Y"),
            # Full month names
            (r"(?:january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2}(?: \d{4})?", "%B %d %Y"),
            (r"\d{1,2} (?:january|february|march|april|may|june|july|august|september|october|november|december)(?: \d{4})?", "%d %B %Y"),
            # With time
            (r".* at \d{1,2}:\d{2}(?: ?[ap]m)?", ""),  # Handled by timeconverter
        ]
        
        for pattern, date_format in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group()
                    if not any(c.isdigit() for c in date_str[-4:]):  # No year provided
                        date_str += f" {now.year}"
                    
                    dt = datetime.strptime(date_str, date_format)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    
                    if dt < now and not any(c.isdigit() for c in date_str[-4:]):
                        dt = dt.replace(year=dt.year + 1)
                    
                    return dt
                except ValueError:
                    continue
        
        return None

    @commands.command(name='remind', aliases=['remindme'], no_pm=True)
    async def remind(self, ctx: commands.Context, *, text: str):
        """Create a reminder using separators:
        - < lower than
        - - hyphen
        - | bar
        - > greater than
        - : colon
        - — em dash
        Examples:
        !remind May 20: camping trip
        !remind 20 May - birthday party
        !remind in 2 hours | remember the staff meeting
        """
        # First try to split by separator
        date_part, reminder_text = self.parse_with_separator(text)
        
        if not reminder_text:
            embed = discord.Embed(
                title="Invalid format",
                description="Please include reminder text after the date.\n"
                           f"Example: `{ctx.prefix}remind May 20, camping trip`",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
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
            view = ReminderPaginator(embeds, self.db, ctx.author.id)
            view.current_page = 0
            view.update_buttons()
            message = await ctx.send(embed=embeds[0], view=view)
            view.message = message
        else:
            # Multiple reminders - paginate
            paginator = ReminderPaginator(embeds, self.db, ctx.author.id)
            message = await ctx.send(embed=embeds[0], view=paginator)
            paginator.message = message
            
    @tasks.loop(seconds=30)
    async def reminder_task(self):
        await self.bot.wait_until_ready()
        now = datetime.now(UTC)
        
        reminders = await self.db.find({"due": {"$lte": now}}).to_list(None)
        log.debug(f"Found {len(reminders)} due reminders at {now.isoformat()}")
        
        for reminder in reminders:
            try:
                channel = None
                if reminder.get("channel_id"):
                    channel = self.bot.get_channel(reminder["channel_id"])
                
                embed = discord.Embed(
                    title='⏰ Reminder',
                    description=reminder["text"],
                    color=self.bot.main_color
                )
                embed.set_footer(text=f'ID: {reminder["_id"]}')
                
                if channel:
                    await channel.send(f'<@{reminder["user_id"]}>', embed=embed)
                else:
                    user = await self.bot.get_or_fetch_user(reminder["user_id"])
                    if user:
                        await user.send(embed=embed)
                
                await self.db.delete_one({"_id": reminder["_id"]})
                
            except Exception as e:
                log.error(f"Failed to send reminder {reminder['_id']}: {e}")
                continue

    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def reminders_admin(self, ctx: commands.Context):
        """Admin reminder management"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all")
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
                name = str(user)
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
            view = ReminderPaginator(embeds, self.db, is_admin=True)
            view.current_page = 0
            view.update_buttons()
            message = await ctx.send(embed=embeds[0], view=view)
            view.message = message
        else:
            # Multiple reminders - paginate
            paginator = ReminderPaginator(embeds, self.db, is_admin=True)
            message = await ctx.send(embed=embeds[0], view=paginator)
            paginator.message = message

    @reminders_admin.command(name="cleanup")
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
