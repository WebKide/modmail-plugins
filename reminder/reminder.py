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
    """Reminder Plugin with reliable scheduling and admin tools"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.reminder_task.start()
    
    async def cog_load(self):
        await self.db.create_index("due")  # Create index for faster queries
        await self.db.create_index("user_id")
    
    async def cog_unload(self):
        self.reminder_task.cancel()

    def parse_natural_date(self, text: str) -> Optional[datetime]:
        """Parse natural language dates like 'May 17' or '18 of April'"""
        now = datetime.now(UTC)
        
        patterns = [
            (r"(?P<month>[A-Za-z]+) (?P<day>\d{1,2})", "%B %d"),
            (r"(?P<day>\d{1,2}) of (?P<month>[A-Za-z]+)", "%d of %B"),
            (r"(?P<month>[A-Za-z]+) (?P<day>\d{1,2}),? (?P<year>\d{4})", "%B %d %Y"),
            (r"(?P<day>\d{1,2}) of (?P<month>[A-Za-z]+),? (?P<year>\d{4})", "%d of %B %Y"),
        ]
        
        for pattern, date_format in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group().lower()
                    if "year" not in match.groupdict():
                        date_str += f" {now.year}"
                    
                    date_str = date_str.replace("of ", "")
                    dt = datetime.strptime(date_str, date_format.replace(" of ", ""))
                    
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    
                    if dt < now:
                        if "year" not in match.groupdict():
                            dt = dt.replace(year=dt.year + 1)
                    return dt
                except ValueError:
                    continue
        return None

    @commands.command(name='remind', aliases=['remindme'], no_pm=True)
    async def remind(self, ctx: commands.Context, *, time_and_text: str):
        """Create a reminder with natural language time"""
        parts = time_and_text.split(maxsplit=1)
        if len(parts) < 2:
            embed = discord.Embed(
                title="Invalid format",
                description="Please provide both a time and reminder text.\n"
                           f"Example: `{ctx.prefix}remind 30 days to renew subscription`",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        duration_part = parts[0]
        text = parts[1]
        
        time_units = ["days", "day", "hours", "hour", "minutes", "minute", "weeks", "week", "months", "month"]
        if len(duration_part.split()) == 1 and any(unit in parts[1].lower().split() for unit in time_units):
            next_word = parts[1].split()[0]
            if next_word.lower() in time_units:
                duration_part = f"{duration_part} {next_word}"
                text = ' '.join(parts[1].split()[1:])
        
        dt = self.parse_natural_date(duration_part)
        
        if dt is None:
            try:
                timeconverter = UserFriendlyTime()
                converted = await timeconverter.convert(ctx=ctx, argument=duration_part, now=datetime.now(UTC))
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
        else:
            dt = dt.replace(tzinfo=UTC)
        
        if dt <= datetime.now(UTC):
            embed = discord.Embed(
                title="Invalid time",
                description="Reminder time must be in the future",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        reminder = {
            "user_id": ctx.author.id,
            "channel_id": None,
            "text": text,
            "due": dt,
            "created_at": datetime.now(UTC)
        }
        
        result = await self.db.insert_one(reminder)
        reminder_id = str(result.inserted_id)
        
        timestamp = utils.format_dt(dt, 'F')
        relative = utils.format_dt(dt, 'R')
        embed = discord.Embed(
            title='✅ Reminder created',
            description=f'**Reminder:** {text}\n'
                       f'**Due:** {timestamp} ({relative})',
            color=discord.Color.green()
        )
        embed.set_footer(text=f'ID: {reminder_id}')
        await ctx.send(embed=embed)
    
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
        """View all active reminders from all users"""
        reminders = await self.db.find().sort([("user_id", 1), ("due", 1)]).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description='There are no active reminders in the system.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        user_groups = {}
        for reminder in reminders:
            user_id = reminder["user_id"]
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(reminder)
        
        embeds = []
        
        for user_id, user_reminders in user_groups.items():
            try:
                user = await self.bot.get_or_fetch_user(user_id)
                name = str(user)
                avatar = user.avatar.url if user.avatar else None
            except:
                name = f"Unknown User ({user_id})"
                avatar = None
            
            soonest = min(user_reminders, key=lambda x: x["due"])
            
            embed = discord.Embed(
                title=f"Reminders for {name}",
                description=f"**Total:** {len(user_reminders)} reminders",
                color=self.bot.main_color
            )
            
            if avatar:
                embed.set_thumbnail(url=avatar)
            
            embed.add_field(
                name="⏰ Next Due",
                value=f"{soonest['text'][:150]}\n{utils.format_dt(soonest['due'], 'F')}",
                inline=False
            )
            
            embed.add_field(
                name="User ID",
                value=f"`{user_id}`",
                inline=True
            )
            
            created_at = soonest.get("created_at", datetime.now(UTC))
            embed.set_footer(text=created_at.strftime("First reminder created on %Y-%m-%d at %H:%M UTC"))
            
            embed._full_list = user_reminders
            embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, *embeds)
        await paginator.run()

    @reminders_admin.command(name="user")
    @commands.has_permissions(administrator=True)
    async def admin_user_reminders(self, ctx: commands.Context, user: Union[discord.User, int]):
        """View reminders for a specific user"""
        user_id = user.id if isinstance(user, discord.User) else user
        
        try:
            user_obj = await self.bot.get_or_fetch_user(user_id)
            name = str(user_obj)
            avatar = user_obj.avatar.url if user_obj.avatar else None
        except:
            user_obj = None
            name = f"Unknown User ({user_id})"
            avatar = None
        
        reminders = await self.db.find({"user_id": user_id}).sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title=f'No reminders for {name}',
                color=self.bot.error_color
            )
            if avatar:
                embed.set_thumbnail(url=avatar)
            return await ctx.send(embed=embed)
        
        embeds = []
        
        for i in range(0, len(reminders), 5):
            current = reminders[i:i+5]
            embed = discord.Embed(
                title=f"Reminders for {name}",
                description=f"Showing {i+1}-{min(i+5, len(reminders))} of {len(reminders)}",
                color=self.bot.main_color
            )
            
            if avatar:
                embed.set_thumbnail(url=avatar)
            
            for reminder in current:
                truncated = (reminder["text"][:150] + '...') if len(reminder["text"]) > 150 else reminder["text"]
                embed.add_field(
                    name=f"⏰ {utils.format_dt(reminder['due'], 'f')} (ID: {reminder['_id']})",
                    value=truncated,
                    inline=False
                )
            
            embed.set_footer(text=f"Page {i//5 + 1}/{(len(reminders)-1)//5 + 1}")
            embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, *embeds)
        await paginator.run()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
    
