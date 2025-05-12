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
    """Paginator for reminder lists with unique button IDs"""
    def __init__(self, embeds: List[discord.Embed], user_id: int):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id

        # Previous button
        self.prev_button = Button(
            emoji="⬅️",
            style=discord.ButtonStyle.blurple,
            custom_id=f"prev_{user_id}_{datetime.now().timestamp()}"
        )
        self.prev_button.callback = self.previous_page
        self.add_item(self.prev_button)

        # Next button
        self.next_button = Button(
            emoji="➡️",
            style=discord.ButtonStyle.blurple,
            custom_id=f"next_{user_id}_{datetime.now().timestamp()}"
        )
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class TimezoneConverter(commands.Converter):
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

class Remind(commands.Cog):
    """Remind plugin with timezone support"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.user_timezones = {}  # Cache for user timezones
        self.reminder_loop.start()
        
    def cog_unload(self):
        self.reminder_loop.cancel()

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

    async def format_time_with_timezone(self, dt: datetime, user_id: int) -> str:
        """Format time for display in user's timezone"""
        user_tz = await self.get_user_timezone(user_id)
        local_dt = dt.astimezone(user_tz)
        return (
            f"{discord.utils.format_dt(local_dt, 'f')}\n"
            f"({discord.utils.format_dt(local_dt, 'R')})"
        )

    @commands.command(name="mytimezone", aliases=["settimezone", "settz"])
    async def set_timezone(self, ctx, timezone: TimezoneConverter):
        """Set your timezone (e.g., `!mytimezone UTC+2`)"""
        offset_minutes = timezone.utcoffset(None).total_seconds() / 60
        
        await self.db.update_one(
            {"_id": f"timezone_{ctx.author.id}"},
            {"$set": {"offset_minutes": offset_minutes}},
            upsert=True
        )
        
        # Update cache
        self.user_timezones[ctx.author.id] = timezone
        
        await ctx.send(
            f"⏰ Your timezone has been set to `{timezone}`\n"
            f"Current time: {discord.utils.format_dt(datetime.now(timezone), 'f')}"
        )

    @commands.command(name="mytime")
    async def show_current_time(self, ctx):
        """Show your current time based on your timezone setting"""
        user_tz = await self.get_user_timezone(ctx.author.id)
        now = datetime.now(user_tz)
        await ctx.send(
            f"⏰ Your current time: {discord.utils.format_dt(now, 'f')}\n"
            f"Timezone: `{user_tz}`"
        )

    @tasks.loop(seconds=60.0)
    async def reminder_loop(self):
        """Check reminders every minute"""
        try:
            now = datetime.now(pytz.UTC)
            reminders = await self.db.find({"due": {"$lte": now}, "status": "active"}).to_list(None)
            
            for reminder in reminders:
                user = self.bot.get_user(reminder["user_id"])
                if not user:
                    continue
                
                # Get user's timezone for display
                user_tz = await self.get_user_timezone(reminder["user_id"])
                local_time = reminder["due"].astimezone(user_tz)
                
                # Try original channel first
                channel = self.bot.get_channel(reminder["channel_id"]) if reminder.get("channel_id") else None
                try:
                    message = (
                        f"⏰ **Reminder** ({local_time.strftime('%Y-%m-%d %H:%M %Z')})\n"
                        f"{reminder['text']}"
                    )
                    
                    if channel:
                        await channel.send(f"{user.mention} {message}")
                    else:
                        await user.send(message)
                except Exception as e:
                    log.error(f"Failed to deliver reminder: {e}")
                
                # Handle recurring
                if reminder.get("recurring"):
                    await self._reschedule_recurring(reminder)
                else:
                    await self.db.delete_one({"_id": reminder["_id"]})

        except Exception as e:
            log.error(f"Reminder loop error: {e}")

    async def _reschedule_recurring(self, reminder: Dict):
        """Reschedule recurring reminders"""
        frequency = reminder["recurring"]
        new_due = parse(reminder["due"]) + (
            timedelta(days=1) if frequency == "daily" else 
            timedelta(weeks=1)
        )
        await self.db.update_one(
            {"_id": reminder["_id"]},
            {"$set": {"due": new_due}}
        )

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
            # Define possible separators (order matters, longest first)
            SEPARATORS = [" to ", " | ", " - ", " / ", " > ", " [", " — "]
            
            # Find the first occurring separator
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
            
            # Split into time_part and reminder_text
            time_part, reminder_text = input_string.split(separator, 1)
            reminder_text = reminder_text.strip()
            
            if not reminder_text:
                return await ctx.send("⚠️ Reminder text cannot be empty!")
            
            # Get user's timezone for parsing
            user_tz = await self.get_user_timezone(ctx.author.id)
            
            # Parse the time with user's timezone context
            settings = {
                'RELATIVE_BASE': datetime.now(user_tz),
                'TIMEZONE': str(user_tz),
                'TO_TIMEZONE': 'UTC'  # We'll store in UTC
            }
            due = dateparser.parse(time_part, settings=settings)
            
            if not due:
                return await ctx.send(
                    "⚠️ Couldn't understand the time. Try formats like:\n"
                    "• `in 5 minutes`\n• `tomorrow at 3pm`\n• `next monday`"
                )
            
            # Ensure timezone is UTC (dateparser should handle this, but just in case)
            due = pytz.UTC.localize(due) if due.tzinfo is None else due.astimezone(pytz.UTC)
            
            # Check if time is in the future
            if due <= datetime.now(pytz.UTC):
                return await ctx.send(
                    f"⏳ **Time must be in the future!**\n"
                    f"You entered: `{await self.format_time_with_timezone(due, ctx.author.id)}`\n"
                    f"(Current time: `{await self.format_time_with_timezone(datetime.now(pytz.UTC), ctx.author.id)}`)"
                )
            
            # Save to database
            await self.db.insert_one({
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "text": reminder_text,
                "due": due,
                "created": datetime.now(pytz.UTC),
                "status": "active"
            })
            
            await ctx.send(
                f"⏰ **Reminder set!**\n"
                f"**When:** {await self.format_time_with_timezone(due, ctx.author.id)}\n"
                f"**Reminder:** {reminder_text}"
            )
            
        except Exception as e:
            await ctx.send(
                f"❌ **Error setting reminder:** {e}\n\n"
                "**Proper Usage Examples:**\n"
                "• `!remind in 2 hours | take out the trash`\n"
                "• `!remind tomorrow at 3pm - buy groceries`\n"
                "• `!remind next monday, finish the report`"
            )

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
            
            # Get user's timezone for display
            user_tz = await self.get_user_timezone(ctx.author.id)
            
            # Create paginated embeds
            embeds = []
            for idx, rem in enumerate(reminders, 1):
                embed = discord.Embed(
                    title=f"⏰ Reminder #{idx}",
                    color=0x00ff00
                )
                
                # Format time information in user's timezone
                local_dt = rem["due"].astimezone(user_tz)
                time_str = (
                    f"{discord.utils.format_dt(local_dt, 'f')}\n"
                    f"({discord.utils.format_dt(local_dt, 'R')})"
                )
                
                # Format reminder text (with smart truncation)
                text = rem["text"]
                if len(text) > 250:
                    text = text[:250] + "..."
                
                embed.add_field(name="⏰ When", value=time_str, inline=False)
                embed.add_field(name="📝 Reminder", value=text, inline=False)
                
                # Add creation time in footer if it exists
                footer_text = f"ID: {rem['_id']}"
                if "created" in rem:
                    created_dt = rem["created"].astimezone(user_tz)
                    created_str = discord.utils.format_dt(created_dt, "R")
                    footer_text = f"Created {created_str} • {footer_text}"
                
                embed.set_footer(text=footer_text)
                
                embeds.append(embed)
            
            # Send paginated view
            paginator = ReminderPaginator(embeds, ctx.author.id)
            await ctx.send(embed=embeds[0], view=paginator)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error fetching reminders",
                description=f"```{str(e)[:1000]}```",  # Truncate long errors
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Remind(bot))
