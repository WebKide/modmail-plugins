from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import os
import re

import discord
from discord.ext import commands, tasks
from discord import utils

from core import checks
from core.models import PermissionLevel
from core.time import UserFriendlyTime
from core.paginator import EmbedPaginatorSession, MessagePaginatorSession


class Reminder(commands.Cog):
    """Reminder Plugin, adapted from:
    
    martinbndr/kyb3r-modmail-plugins/reminder@master

    If you want the original, simply search for it on GitHub
    """
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.config = None
        self.default_config = {"_id": "reminder"}
        
    async def cog_load(self):
        self.config = await self.db.find_one({"_id": "reminder"})
        if self.config is None:
            self.config = self.default_config
            await self.update_config()
        self.reminder_task.start()
    
    async def cog_unload(self):
        self.reminder_task.cancel()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "reminder"},
            {"$set": self.config},
            upsert=True,
        )
        
    async def get_insert_userdata(self, ctx: commands.Context):
        if str(ctx.author.id) not in self.config:
            self.config[str(ctx.author.id)] = {
                "reminder_id": 0,
                "reminders": {}
            }
            await self.update_config()
        
        self.config[str(ctx.author.id)]["reminder_id"] += 1
        reminder_id = self.config[str(ctx.author.id)]["reminder_id"]
        await self.update_config()
        return reminder_id

    def parse_natural_date(self, text: str) -> Optional[datetime]:
        """Parse natural language dates like 'May 17' or '18 of April'"""
        now = datetime.now()
        
        # Patterns to match
        patterns = [
            (r"(?P<month>[A-Za-z]+) (?P<day>\d{1,2})", "%B %d"),  # May 17
            (r"(?P<day>\d{1,2}) of (?P<month>[A-Za-z]+)", "%d of %B"),  # 17 of May
            (r"(?P<month>[A-Za-z]+) (?P<day>\d{1,2}),? (?P<year>\d{4})", "%B %d %Y"),  # May 17 2023
            (r"(?P<day>\d{1,2}) of (?P<month>[A-Za-z]+),? (?P<year>\d{4})", "%d of %B %Y"),  # 17 of May 2023
        ]
        
        for pattern, date_format in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Construct a date string without year (assume current year)
                    date_str = match.group().lower()
                    if "year" not in match.groupdict():
                        date_str += f" {now.year}"
                    
                    # Clean up the date string for parsing
                    date_str = date_str.replace("of ", "")
                    
                    dt = datetime.strptime(date_str, date_format.replace(" of ", ""))
                    if dt < now:
                        if "year" not in match.groupdict():
                            dt = dt.replace(year=dt.year + 1)
                    return dt
                except ValueError:
                    continue
        return None

    @commands.command(name='remind', aliases=['remindme'], no_pm=True)
    async def remind(self, ctx: commands.Context, *, time_and_text: str):
        """Create a reminder
        Usage:
        {prefix}remind 1h30m Do the thing
        {prefix}remind May 17 Birthday party!
        {prefix}remind 18 of April Pay rent
        {prefix}remind 30 days to renew subscription
        """
        # Split the input into duration and reminder text
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
        
        # Check for multi-word durations (like "30 days")
        time_units = ["days", "day", "hours", "hour", "minutes", "minute", "weeks", "week", "months", "month"]
        if len(duration_part.split()) == 1 and any(unit in parts[1].lower().split() for unit in time_units):
            # Handle cases like "30 days to renew"
            next_word = parts[1].split()[0]
            if next_word.lower() in time_units:
                duration_part = f"{duration_part} {next_word}"
                text = ' '.join(parts[1].split()[1:])
        
        # First try natural date parsing
        dt = self.parse_natural_date(duration_part)
        
        # If natural parsing fails, use the time converter
        if dt is None:
            try:
                timeconverter = UserFriendlyTime()
                converted = await timeconverter.convert(ctx=ctx, argument=duration_part, now=datetime.now())
                dt = converted.dt
            except commands.BadArgument as e:
                embed = discord.Embed(
                    title="Invalid time format",
                    description=str(e),
                    color=self.bot.error_color
                )
                return await ctx.send(embed=embed)
        
        reminder_id = await self.get_insert_userdata(ctx)
        
        reminder_data = {
            "end": dt,
            "channel_id": None,  # Default to DM
            "text": text
        }
        
        self.config[str(ctx.author.id)]["reminders"][str(reminder_id)] = reminder_data
        await self.update_config()
        
        timestamp = utils.format_dt(dt, 'F')
        relative = utils.format_dt(dt, 'R')
        embed = discord.Embed(
            title='Reminder created',
            description=f'Your reminder has been created successfully!\n\n'
                       f'**Reminder:** {text}\n'
                       f'**Due:** {timestamp} ({relative})',
            color=discord.Color.green()
        )
        embed.set_footer(text=f'Reminder ID: {reminder_id}')
        await ctx.send(embed=embed)
    
    @commands.command(name='delreminder', aliases=['forgetreminder'], no_pm=True)
    async def delreminder(self, ctx: commands.Context, reminder_id: int):
        """Delete a reminder"""
        if str(ctx.author.id) not in self.config:
            embed = discord.Embed(
                title='No reminders found',
                description='You do not have any active reminders!',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        user_reminders = self.config[str(ctx.author.id)]["reminders"]
        if str(reminder_id) not in user_reminders:
            embed = discord.Embed(
                title='Reminder not found',
                description=f'A reminder with the given ID ``{reminder_id}`` was not found.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        user_reminders.pop(str(reminder_id))
        await self.update_config()
        
        embed = discord.Embed(
            title='Reminder deleted',
            description=f'Your reminder ``{reminder_id}`` has been deleted successfully!',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
            
    @commands.command(name='reminders', aliases=['listreminders','lreminders'], no_pm=True)
    async def reminders(self, ctx: commands.Context):
        """List your reminders"""
        if str(ctx.author.id) not in self.config or not self.config[str(ctx.author.id)]["reminders"]:
            embed = discord.Embed(
                title='No reminders found',
                description='You do not have any active reminders!',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        user_reminders = self.config[str(ctx.author.id)]["reminders"]
        embeds = []
        
        for reminder_id, reminder in user_reminders.items():
            remind_location = "Direct Message"
            if reminder["channel_id"] is not None:
                remind_location = f'<#{reminder["channel_id"]}>'
                
            timestamp = utils.format_dt(reminder["end"], "F")
            relative = utils.format_dt(reminder["end"], "R")
            
            embed = discord.Embed(
                title=f'Reminder {reminder_id}',
                description=f'**Reminder:** {reminder["text"]}\n'
                           f'**Due:** {timestamp} ({relative})\n'
                           f'**Channel:** {remind_location}',
                color=self.bot.main_color
            )
            embeds.append(embed)
            
        if not embeds:
            embed = discord.Embed(
                title='No reminders found',
                description='You do not have any active reminders!',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        session = EmbedPaginatorSession(ctx, *embeds)
        await session.run()
            
    @tasks.loop(seconds=10)
    async def reminder_task(self):
        await self.bot.wait_until_ready()
        if not self.config:
            return
            
        for user_id, user_data in self.config.items():
            if user_id == '_id':
                continue
                
            if "reminders" not in user_data:
                continue
                
            reminders = user_data["reminders"].copy()
            now = datetime.now()
            
            for reminder_id, reminder in reminders.items():
                if now >= reminder["end"]:
                    # Send the reminder
                    try:
                        channel = None
                        if reminder["channel_id"] is not None:
                            channel = self.bot.get_channel(reminder["channel_id"])
                        
                        embed = discord.Embed(
                            title='⏰ Reminder',
                            description=reminder["text"],
                            color=self.bot.main_color
                        )
                        embed.set_footer(text=f'Reminder ID: {reminder_id}')
                        
                        if channel:
                            await channel.send(f'<@{user_id}>', embed=embed)
                        else:
                            user = await self.bot.get_or_fetch_user(int(user_id))
                            if user:
                                await user.send(embed=embed)
                    except Exception as e:
                        print(f"Failed to send reminder: {e}")
                    
                    # Remove the reminder
                    self.config[user_id]["reminders"].pop(reminder_id)
                    await self.update_config()

async def setup(bot):
    await bot.add_cog(Reminder(bot))
  
