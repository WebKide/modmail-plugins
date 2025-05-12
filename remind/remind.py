# !plugin update WebKide/modmail-plugins/remind@master
import logging
from datetime import datetime, timedelta
from typing import List, Dict

import dateparser
import pytz
from dateutil.parser import parse

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button


log = logging.getLogger("Modmail")

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

class Remind(commands.Cog):
    """Remind plugin by Webkide"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.reminder_loop.start()
        
    def cog_unload(self):
        self.reminder_loop.cancel()

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
                
                # Try original channel first
                channel = self.bot.get_channel(reminder["channel_id"]) if reminder.get("channel_id") else None
                try:
                    if channel:
                        await channel.send(f"{user.mention} Reminder: {reminder['text']}")
                    else:
                        await user.send(f"Reminder: {reminder['text']}")
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
            
            # Parse the time
            settings = {'RELATIVE_BASE': datetime.now(pytz.UTC)}
            due = dateparser.parse(time_part, settings=settings)
            
            if not due:
                return await ctx.send(
                    "⚠️ Couldn't understand the time. Try formats like:\n"
                    "• `in 5 minutes`\n• `tomorrow at 3pm`\n• `next monday`"
                )
            
            # Ensure timezone is UTC
            due = pytz.UTC.localize(due) if due.tzinfo is None else due.astimezone(pytz.UTC)
            
            # Check if time is in the future
            if due <= datetime.now(pytz.UTC):
                return await ctx.send(
                    f"⏳ **Time must be in the future!**\n"
                    f"You entered: `{discord.utils.format_dt(due, 'f')}`\n"
                    f"(Current time: `{discord.utils.format_dt(datetime.now(pytz.UTC), 'f')}`)"
                )
            
            # Save to database
            await self.db.insert_one({
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "text": reminder_text,
                "due": due,
                "status": "active"
            })
            
            await ctx.send(
                f"⏰ **Reminder set!**\n"
                f"**When:** {discord.utils.format_dt(due, 'f')} ({discord.utils.format_dt(due, 'R')})\n"
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
                embed = discord.Embed(
                    title=f"⏰ Reminder #{idx}",
                    color=0x00ff00,
                    timestamp=rem["due"]
                )
                
                # Format time information
                time_str = (
                    f"{discord.utils.format_dt(rem['due'], 'f')}\n"
                    f"({discord.utils.format_dt(rem['due'], 'R')})"
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
                    created_str = discord.utils.format_dt(rem["created"], "R")
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
