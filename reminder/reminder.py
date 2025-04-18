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
    """Reminder Plugin with MongoDB persistence"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.reminder_task.start()
    
    async def cog_unload(self):
        self.reminder_task.cancel()

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
        
        # Store reminder in database
        reminder = {
            "user_id": ctx.author.id,
            "channel_id": None,  # Default to DM
            "text": text,
            "due": dt,
            "created_at": datetime.now()
        }
        
        result = await self.db.insert_one(reminder)
        reminder_id = str(result.inserted_id)
        
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
    async def delreminder(self, ctx: commands.Context, reminder_id: str):
        """Delete a reminder"""
        try:
            from bson import ObjectId
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
            title='Reminder deleted',
            description='Your reminder has been deleted successfully!',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
            
    @commands.command(name='reminders', aliases=['listreminders','lreminders'], no_pm=True)
    async def reminders(self, ctx: commands.Context):
        """List your reminders"""
        reminders = await self.db.find({"user_id": ctx.author.id}).sort("due", 1).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description='You do not have any active reminders!',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
            
        embeds = []
        
        for reminder in reminders:
            remind_location = "Direct Message"
            if reminder.get("channel_id"):
                remind_location = f'<#{reminder["channel_id"]}>'
                
            timestamp = utils.format_dt(reminder["due"], "F")
            relative = utils.format_dt(reminder["due"], "R")
            
            embed = discord.Embed(
                title=f'Reminder {reminder["_id"]}',
                description=f'**Reminder:** {reminder["text"]}\n'
                           f'**Due:** {timestamp} ({relative})\n'
                           f'**Channel:** {remind_location}',
                color=self.bot.main_color
            )
            embed.set_footer(text=f'Created: {utils.format_dt(reminder["created_at"], "R")}')
            embeds.append(embed)
            
        session = EmbedPaginatorSession(ctx, *embeds)
        await session.run()
            
    @tasks.loop(seconds=30)
    async def reminder_task(self):
        await self.bot.wait_until_ready()
        
        now = datetime.now()
        # Find all reminders that are due
        reminders = await self.db.find({"due": {"$lte": now}}).to_list(None)
        
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
                embed.set_footer(text=f'Reminder ID: {reminder["_id"]}')
                
                if channel:
                    await channel.send(f'<@{reminder["user_id"]}>', embed=embed)
                else:
                    user = await self.bot.get_or_fetch_user(reminder["user_id"])
                    if user:
                        await user.send(embed=embed)
                
                # Delete the reminder after sending
                await self.db.delete_one({"_id": reminder["_id"]})
                
            except Exception as e:
                print(f"Failed to send reminder: {e}")
                # If DM failed, try again later
                continue

    @commands.group(name="remindersadmin", aliases=["ra"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def reminders_admin(self, ctx: commands.Context):
        """Admin command group for managing reminders"""
        await ctx.send_help(ctx.command)

    @reminders_admin.command(name="all")
    @commands.has_permissions(administrator=True)
    async def admin_all_reminders(self, ctx: commands.Context):
        """View all active reminders from all users (paginated)"""
        reminders = await self.db.find().sort([("user_id", 1), ("due", 1)]).to_list(None)
        
        if not reminders:
            embed = discord.Embed(
                title='No reminders found',
                description='There are no active reminders in the system.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        # Group reminders by user
        user_reminders = {}
        for reminder in reminders:
            user_id = reminder["user_id"]
            if user_id not in user_reminders:
                user_reminders[user_id] = []
            user_reminders[user_id].append(reminder)
        
        embeds = []
        
        for user_id, reminders_list in user_reminders.items():
            try:
                user = await self.bot.get_or_fetch_user(user_id)
                username = str(user)
                avatar = user.avatar.url if user.avatar else user.default_avatar.url
            except:
                username = f"Unknown User ({user_id})"
                avatar = None
            
            # Sort reminders by due date
            reminders_list.sort(key=lambda x: x["due"])
            
            # Create description with truncated reminders
            description = ""
            for reminder in reminders_list[:3]:  # Show up to 3 in description
                truncated_text = (reminder["text"][:75] + '...') if len(reminder["text"]) > 75 else reminder["text"]
                relative_time = utils.format_dt(reminder["due"], "R")
                description += f"• {truncated_text} ({relative_time})\n"
            
            if len(reminders_list) > 3:
                description += f"\n...and {len(reminders_list) - 3} more reminders"
            
            # Create embed
            embed = discord.Embed(
                title=f"Reminders for {username}",
                description=description,
                color=self.bot.main_color
            )
            
            if avatar:
                embed.set_thumbnail(url=avatar)
            
            # Add soonest reminder as a field
            soonest = reminders_list[0]
            embed.add_field(
                name="⏰ Next Reminder",
                value=f"{soonest['text'][:100]}\nDue: {utils.format_dt(soonest['due'], 'f')}",
                inline=False
            )
            
            # Add user ID field
            embed.add_field(
                name="User ID",
                value=f"`{user_id}`",
                inline=True
            )
            
            # Add total reminders field
            embed.add_field(
                name="Total Reminders",
                value=str(len(reminders_list)),
                inline=True
            )
            
            # Format created_at timestamp
            created_at = soonest.get("created_at", datetime.now())
            footer_text = created_at.strftime("Created: %Y-%m-%d %H:%M")
            embed.set_footer(text=footer_text)
            
            # Store the full reminders list in the embed for pagination
            embed._reminders_list = reminders_list
            embed._user = user if 'user' in locals() else None
            embeds.append(embed)
        
        # Custom paginator to handle user-specific pagination
        class ReminderPaginator(EmbedPaginatorSession):
            async def update_embed(self, embed, page_idx):
                reminders_list = embed._reminders_list
                user = embed._user
                
                # Update description with current page's reminders
                start_idx = page_idx * 3
                end_idx = start_idx + 3
                current_reminders = reminders_list[start_idx:end_idx]
                
                description = ""
                for reminder in current_reminders:
                    truncated_text = (reminder["text"][:75] + '...') if len(reminder["text"]) > 75 else reminder["text"]
                    relative_time = utils.format_dt(reminder["due"], "R")
                    description += f"• {truncated_text} ({relative_time})\n"
                
                embed.description = description
                
                # Update next reminder field
                if start_idx < len(reminders_list):
                    next_reminder = reminders_list[start_idx]
                    embed.set_field_at(
                        0,
                        name="⏰ Next Reminder",
                        value=f"{next_reminder['text'][:100]}\nDue: {utils.format_dt(next_reminder['due'], 'f')}",
                        inline=False
                    )
                
                # Update page indicator
                total_pages = (len(reminders_list) + 2) // 3
                embed.set_footer(text=f"{embed.footer.text} • Page {page_idx + 1}/{total_pages}")
                return embed
        
        paginator = ReminderPaginator(ctx, *embeds)
        await paginator.run()

    @reminders_admin.command(name="user")
    @commands.has_permissions(administrator=True)
    async def admin_user_reminders(self, ctx: commands.Context, user: Union[discord.User, int]):
        """View all reminders for a specific user"""
        user_id = user.id if isinstance(user, discord.User) else user
        try:
            user_obj = await self.bot.get_or_fetch_user(user_id)
        except:
            user_obj = None
        
        reminders = await self.db.find({"user_id": user_id}).sort("due", 1).to_list(None)
        
        if not reminders:
            username = f"Unknown User ({user_id})" if user_obj is None else str(user_obj)
            embed = discord.Embed(
                title=f'No reminders found for {username}',
                description='This user has no active reminders.',
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)
        
        # Create paginated embeds
        embeds = []
        avatar = user_obj.avatar.url if user_obj and user_obj.avatar else None
        
        for i in range(0, len(reminders), 5):  # 5 reminders per page
            current_reminders = reminders[i:i+5]
            
            embed = discord.Embed(
                title=f"Reminders for {str(user_obj) if user_obj else f'Unknown User ({user_id})'}",
                color=self.bot.main_color
            )
            
            if avatar:
                embed.set_thumbnail(url=avatar)
            
            for reminder in current_reminders:
                truncated_text = (reminder["text"][:100] + '...') if len(reminder["text"]) > 100 else reminder["text"]
                embed.add_field(
                    name=f"⏰ {utils.format_dt(reminder['due'], 'f')} (ID: {reminder['_id']})",
                    value=truncated_text,
                    inline=False
                )
            
            created_at = current_reminders[0].get("created_at", datetime.now())
            embed.set_footer(text=created_at.strftime("Created: %Y-%m-%d %H:%M") + f" | Page {i//5 + 1}/{(len(reminders)-1)//5 + 1}")
            
            embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, *embeds)
        await paginator.run()
        
async def setup(bot):
    await bot.add_cog(Reminder(bot))
    
