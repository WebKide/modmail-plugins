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
from bson import ObjectId

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime
from core.paginator import EmbedPaginatorSession, MessagePaginatorSession

UTC = timezone.utc
log = logging.getLogger(__name__)

class Reminder(commands.Cog):
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
        separators = [',', '-', '|', '>', ':']
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
        """Create a reminder using separators: , - | > :
        Examples:
        !remind May 20, camping trip
        !remind 20 May - birthday party
        !remind in 2 hours | don't forget the meeting
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
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('🚮')  # Add delete reaction

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reminder deletion via reaction"""
        if user.bot or reaction.emoji != '🚮':
            return
        
        msg = reaction.message
        if not msg.embeds or not msg.embeds[0].footer.text:
            return
            
        # Extract reminder ID from footer
        footer = msg.embeds[0].footer.text
        if not footer.startswith('ID: '):
            return
            
        reminder_id = footer[4:]
        
        try:
            reminder = await self.db.find_one({"_id": ObjectId(reminder_id)})
            if not reminder:
                return
                
            # Check if user is admin or reminder owner
            if (user.id != reminder["user_id"] and 
                not reaction.message.channel.permissions_for(user).administrator):
                return
                
            await self.db.delete_one({"_id": ObjectId(reminder_id)})
            embed = msg.embeds[0].copy()
            embed.title = '🗑️ Reminder Deleted'
            embed.color = discord.Color.red()
            await msg.edit(embed=embed)
            await msg.clear_reaction('🚮')
            
        except Exception as e:
            log.error(f"Error deleting reminder: {e}")

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
            
    @commands.command(name='reminders', aliases=['listreminders','lreminders'], no_pm=True)
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
        
        for i in range(0, len(reminders), 5):
            current = reminders[i:i+5]
            embed = discord.Embed(
                title=f'Your Reminders ({len(reminders)} total)',
                color=self.bot.main_color
            )
            
            for reminder in current:
                truncated = (reminder["text"][:100] + '...') if len(reminder["text"]) > 100 else reminder["text"]
                embed.add_field(
                    name=f"⏰ {utils.format_dt(reminder['due'], 'f')} (ID: {reminder['_id']})",
                    value=truncated,
                    inline=False
                )
            
            embed.set_footer(text=f"Page {i//5 + 1}/{(len(reminders)-1)//5 + 1}")
            embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, *embeds)
        await paginator.run()
            
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
        reminders = await self.db.find().sort([("user_id", 1), ("due", 1)]).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        embeds = []
        for reminder in reminders:
            try:
                user = await self.bot.get_or_fetch_user(reminder["user_id"])
                name = str(user)
                avatar = user.avatar.url if user.avatar else None
            except:
                name = f"Unknown User ({reminder['user_id']})"
                avatar = None
            
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
                     f"Created: {utils.format_dt(reminder['created_at'], 'R')}",
                inline=False
            )
            
            embed.set_footer(text=f"Reminder ID: {reminder['_id']}")
            embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, *embeds)
        paginator.customize_button('🚮', style=discord.ButtonStyle.danger)
        await paginator.run()
        
        # Add delete reaction to each page
        for msg in paginator.pages:
            await msg.add_reaction('🚮')

async def setup(bot):
    await bot.add_cog(Reminder(bot))
