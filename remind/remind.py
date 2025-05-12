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
    """Enhanced paginator for reminder lists with delete functionality"""
    def __init__(self, embeds: List[discord.Embed], user_id: int, original_message: discord.Message, cog):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.original_message = original_message
        self.deleted = False
        self.cog = cog  # Reference to the main cog for DB access

        # Add buttons
        self.add_buttons()

    def add_buttons(self):
        """Dynamically add buttons based on page count"""
        # Clear existing buttons
        self.clear_items()

        # Previous button
        if len(self.embeds) > 1:
            prev_button = Button(
                emoji="𝖯𝖱𝖤𝖵",
                style=discord.ButtonStyle.blurple,
                custom_id=f"prev_{self.user_id}_{datetime.now().timestamp()}"
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

        # Delete button
        delete_button = Button(
            emoji="𝖣𝖤𝖫 𝖱𝖤𝖬𝖨𝖭𝖣𝖤𝖱",
            style=discord.ButtonStyle.red,
            custom_id=f"delete_{self.user_id}_{datetime.now().timestamp()}"
        )
        delete_button.callback = self.delete_reminder
        self.add_item(delete_button)

        # Next button
        if len(self.embeds) > 1:
            next_button = Button(
                emoji="𝖭𝖤𝖷𝖳",
                style=discord.ButtonStyle.blurple,
                custom_id=f"next_{self.user_id}_{datetime.now().timestamp()}"
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def create_embed(self, reminder_data: dict, user: discord.User) -> discord.Embed:
        """Create a styled embed for a reminder"""
        user_tz = await self.cog.get_user_timezone(self.user_id)
        local_dt = reminder_data["due"].astimezone(user_tz)
        
        embed = discord.Embed(
            description=f"### 📝 Reminder:\n# {reminder_data['text']}",
            color=discord.Color(0xd0d88f),
            timestamp=reminder_data["due"]
        )
        
        # Set author with user's avatar
        embed.set_author(
            name=f"⏰ Reminder #{self.current_page + 1} for {user.display_name}",
            icon_url=user.avatar.url
        )
        
        # Set thumbnail and image
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        # Add formatted time field
        time_str = (
            f"```cs\n"
            f"{local_dt.strftime('%d %B %Y %H:%M')}\n"
            f"[{discord.utils.format_dt(reminder_data['due'], 'R')}]\n"
            f"```"
        )
        embed.add_field(
            name="📆 When:",
            value=time_str,
            inline=False
        )
        
        # Add footer with ID
        embed.set_footer(text=f"ID: {reminder_data['_id']}")
        
        return embed

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_embed(interaction)

    async def delete_reminder(self, interaction: discord.Interaction):
        """Handle reminder deletion"""
        reminder_id = self.embeds[self.current_page].footer.text.split("ID: ")[1]
        await self.cog.db.delete_one({"_id": reminder_id})
        
        # Remove the deleted reminder from our list
        del self.embeds[self.current_page]
        
        if not self.embeds:
            # No reminders left
            embed = discord.Embed(
                description="🗑️ Reminder deleted! You have no more reminders.",
                color=discord.Color.red()
            )
            self.deleted = True
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        # Adjust current page if needed
        if self.current_page >= len(self.embeds):
            self.current_page = len(self.embeds) - 1
        
        # Update buttons
        self.add_buttons()
        await self.update_embed(interaction, confirmation="🗑️ Reminder deleted!")

    async def update_embed(self, interaction: discord.Interaction, confirmation: str = None):
        """Update the embed with current page and optional confirmation message"""
        user = await self.cog.bot.fetch_user(self.user_id)
        embed = await self.create_embed({
            "_id": self.embeds[self.current_page].footer.text.split("ID: ")[1],
            "due": self.embeds[self.current_page].timestamp,
            "text": self.embeds[self.current_page].description.split("### 📝 Reminder:\n")[1]
        }, user)
        
        if confirmation:
            embed.set_footer(text=f"{confirmation}\n{embed.footer.text}")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        """Remove buttons when view times out"""
        if not self.deleted:
            try:
                await self.original_message.edit(view=None)
            except discord.NotFound:
                pass

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

    async def get_user_timezone(self, user_id: int) -> pytz.BaseTzInfo:
        """Get user's timezone from DB or cache with proper fallback"""
        if user_id in self.user_timezones:
            return self.user_timezones[user_id]
        
        user_data = await self.db.find_one({"_id": f"timezone_{user_id}"})
        if user_data:
            try:
                # Handle both offset minutes and timezone string
                if "offset_minutes" in user_data:
                    tz = pytz.FixedOffset(user_data["offset_minutes"])
                elif "timezone" in user_data:
                    tz = pytz.timezone(user_data["timezone"])
                else:
                    tz = pytz.UTC
                
                self.user_timezones[user_id] = tz
                return tz
            except Exception:
                pass
        
        # Default to UTC if not set or invalid
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
                'TO_TIMEZONE': 'UTC'
            }
            
            # First try parsing with timezone awareness
            due = dateparser.parse(time_part, settings=settings)
            
            # Fallback if timezone parsing fails
            if not due:
                due = dateparser.parse(time_part)
                if not due:
                    return await ctx.send("⚠️ Couldn't understand the time format.")
                
                # Apply user's timezone to the naive datetime
                due = user_tz.localize(due)
            
            # Convert to UTC for storage
            due = due.astimezone(pytz.UTC)
            
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
            
            # Create paginated embeds
            embeds = []
            for idx, rem in enumerate(reminders, 1):
                # Get user's timezone for display
                user_tz = await self.get_user_timezone(ctx.author.id)
                local_dt = rem["due"].astimezone(user_tz)
                
                embed = discord.Embed(
                    description=f"### 📝 Reminder:\n{rem['text']}",
                    color=discord.Color(0xd0d88f),
                    timestamp=rem["due"]
                )
                
                # Set author with user's avatar
                embed.set_author(
                    name=f"⏰ Reminder #{idx} for {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url
                )
                
                # Set thumbnail
                embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
                
                # Add formatted time field
                time_str = (
                    f"```cs\n"
                    f"{local_dt.strftime('%d %B %Y %H:%M')}\n"
                    f"[{discord.utils.format_dt(rem['due'], 'R')}]\n"
                    f"```"
                )
                embed.add_field(
                    name="📆 When:",
                    value=time_str,
                    inline=False
                )
                
                # Add footer with ID
                embed.set_footer(text=f"ID: {rem['_id']}")
                
                embeds.append(embed)
            
            # Send paginated view
            message = await ctx.send(embed=embeds[0])
            paginator = ReminderPaginator(embeds, ctx.author.id, message, self)
            await message.edit(view=paginator)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error fetching reminders",
                description=f"```{str(e)[:1000]}```",  # Truncate long errors
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Remind(bot))
