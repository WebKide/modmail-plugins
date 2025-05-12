import logging
from datetime import datetime, timedelta
import pytz
import discord
from dateutil.parser import parse
from discord.ext import commands, tasks
from discord.ui import View, Button
from typing import List, Dict

log = logging.getLogger("Modmail")

class ReminderPaginator(View):
    """Basic paginator for reminder lists"""
    def __init__(self, embeds: List[discord.Embed], user_id: int):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id

        # Add buttons
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: Button):
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
    async def remind(self, ctx, when: str, *, text: str):
        """Set a reminder - Usage: !remind [when] [text]"""
        try:
            due = parse(when, fuzzy=True)
            if due.tzinfo is None:
                due = pytz.UTC.localize(due)
                
            if due <= datetime.now(pytz.UTC):
                return await ctx.send("Time must be in the future!")
                
            reminder = {
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "text": text,
                "due": due,
                "created": datetime.now(pytz.UTC),
                "status": "active"
            }
            
            await self.db.insert_one(reminder)
            await ctx.send(f"Reminder set for {discord.utils.format_dt(due, 'R')}!")
            
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command(aliases=["myreminders"])
    async def reminders(self, ctx):
        """List your active reminders"""
        reminders = await self.db.find({"user_id": ctx.author.id, "status": "active"}).to_list(None)
        
        if not reminders:
            return await ctx.send("No active reminders!")
            
        embeds = []
        for idx, rem in enumerate(reminders, 1):
            embed = discord.Embed(title=f"Reminder #{idx}", color=0x00ff00)
            embed.add_field(name="When", value=discord.utils.format_dt(rem["due"], "R"))
            embed.add_field(name="Text", value=rem["text"][:100] + ("..." if len(rem["text"]) > 100 else ""))
            embeds.append(embed)
            
        paginator = ReminderPaginator(embeds, ctx.author.id)
        await ctx.send(embed=embeds[0], view=paginator)

async def setup(bot):
    await bot.add_cog(Remind(bot))
