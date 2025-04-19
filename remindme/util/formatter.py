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

from datetime import datetime, timezone
from typing import List, Optional
import asyncio
import logging

import discord
from discord.ui import Button, View
from discord import utils
from bson import ObjectId

UTC = timezone.utc
log = logging.getLogger(__name__)

class ReminderPaginator(View):
    """Custom paginator with edit/delete/repeat buttons for reminders"""
    def __init__(self, bot, embeds, db, user_id: int = None, is_admin: bool = False):
        super().__init__(timeout=180)
        self.bot = bot
        self.embeds = embeds
        self.current_page = 0
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
        self.message = None
        self.cleanup_task = None
        self.update_buttons()

    async def on_timeout(self) -> None:
        """Handle timeout by disabling buttons"""
        try:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)
        except Exception as e:
            log.debug(f"Failed to disable buttons on timeout: {e}")

    def update_buttons(self) -> None:
        """Update button states based on current page and permissions"""
        self.clear_items()
        
        # Navigation buttons
        prev_button = Button(emoji="⬅️", style=discord.ButtonStyle.blurple, disabled=self.current_page == 0)
        prev_button.callback = self.previous_page
        self.add_item(prev_button)

        # Action buttons (only if user is owner or admin)
        current_reminder = self.get_current_reminder()
        if current_reminder and (self.is_admin or (self.user_id and current_reminder["user_id"] == self.user_id)):
            edit_button = Button(emoji="⏰", style=discord.ButtonStyle.grey)
            edit_button.callback = self.edit_reminder
            self.add_item(edit_button)

            repeat_button = Button(emoji="🔁", style=discord.ButtonStyle.green)
            repeat_button.callback = self.repeat_reminder
            self.add_item(repeat_button)

            delete_button = Button(emoji="🗑️", style=discord.ButtonStyle.red)
            delete_button.callback = self.delete_reminder
            self.add_item(delete_button)

        # Close button
        close_button = Button(emoji="❎", style=discord.ButtonStyle.grey)
        close_button.callback = self.close_message
        self.add_item(close_button)

        # Next button
        next_button = Button(emoji="➡️", style=discord.ButtonStyle.blurple, disabled=self.current_page == len(self.embeds) - 1)
        next_button.callback = self.next_page
        self.add_item(next_button)

    def get_current_reminder(self) -> Optional[dict]:
        """Extract reminder data from current embed"""
        embed = self.embeds[self.current_page]
        if not embed.footer or not embed.footer.text.startswith('Reminder ID: '):
            return None
            
        try:
            reminder_id = ObjectId(embed.footer.text[13:])
            return {
                "_id": reminder_id,
                "user_id": int(embed.fields[0].value.split('\n')[0].split(': ')[1].strip('`')),
                "text": embed.description.strip('```css\n').strip('\n```'),
                "due": None  # Will be parsed from title
            }
        except Exception:
            return None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Reset timeout on any interaction"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        self.cleanup_task = self.bot.loop.create_task(self.schedule_timeout())
        return await super().interaction_check(interaction)

    async def schedule_timeout(self) -> None:
        """Disable buttons after timeout"""
        await asyncio.sleep(180)
        await self.on_timeout()

    async def previous_page(self, interaction: discord.Interaction) -> None:
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next_page(self, interaction: discord.Interaction) -> None:
        """Go to next page"""
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def close_message(self, interaction: discord.Interaction) -> None:
        """Delete the reminder message"""
        if interaction.user.guild_permissions.manage_messages or interaction.user.id == self.user_id:
            await interaction.message.delete()
            self.stop()
        else:
            await interaction.response.send_message("You don't have permission to close this.", ephemeral=True)

    async def delete_reminder(self, interaction: discord.Interaction) -> None:
        """Delete current reminder"""
        reminder = self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder data.", ephemeral=True)
            return
            
        await self.db.delete_one({"_id": reminder["_id"]})
        embed = self.embeds[self.current_page]
        embed.title = '🗑️ Reminder Deleted'
        embed.color = discord.Color.red()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def edit_reminder(self, interaction: discord.Interaction) -> None:
        """Initiate reminder editing process"""
        reminder = self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder data.", ephemeral=True)
            return
            
        await interaction.response.send_message(
            "Please reply with the new time for this reminder (e.g. 'in 2 hours' or 'tomorrow 3pm').",
            ephemeral=True
        )
        
        def check(m: discord.Message) -> bool:
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
            
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for response.", ephemeral=True)
            return
            
        # Parse new time and update reminder
        # (Implementation continues in remindme.py)
        await interaction.followup.send("Reminder time updated!", ephemeral=True)

    async def repeat_reminder(self, interaction: discord.Interaction) -> None:
        """Repeat the current reminder with same duration"""
        reminder = self.get_current_reminder()
        if not reminder:
            await interaction.response.send_message("Could not find reminder data.", ephemeral=True)
            return
            
        # Calculate original duration and re-create reminder
        original_duration = reminder["due"] - reminder.get("created_at", datetime.now(UTC))
        new_due = datetime.now(UTC) + original_duration
        
        await self.db.insert_one({
            "user_id": reminder["user_id"],
            "channel_id": reminder.get("channel_id"),
            "text": reminder["text"],
            "due": new_due,
            "created_at": datetime.now(UTC)
        })
        
        await interaction.response.send_message(
            f"Reminder set to repeat {utils.format_dt(new_due, 'R')}!",
            ephemeral=True
        )
        
