# modmail-plugins/remindmepro/ui/edit_reminder_modals.py
from discord.ui import Modal, TextInput
from discord import TextStyle
import discord
from datetime import datetime
from dateutil.parser import parse

from ..corefunc.schemas import Reminder
from ..corefunc.user_settings import UserSettings
from ..corefunc.utilities import validate_future_time

class EditReminderModal(Modal, title="Edit Reminder"):
    """Modal for editing reminder details"""
    
    new_text = TextInput(
        label="New Reminder Text",
        placeholder="What would you like to be reminded about?",
        default="",  # Will be set in __init__
        style=TextStyle.long,
        required=False
    )
    
    new_time = TextInput(
        label="New Date/Time",
        placeholder="e.g. 'tomorrow at 3pm' or 'April 1'",
        default="",  # Will be set in __init__
        style=TextStyle.short,
        required=False
    )

    def __init__(self, reminder: Reminder):
        super().__init__()
        self.reminder = reminder
        self.new_text.default = reminder.text
        self.new_time.default = discord.utils.format_dt(reminder.due, "f")

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            updates = {}
            text_input = self.new_text.value.strip()
            time_input = self.new_time.value.strip()
            
            if text_input and text_input != self.reminder.text:
                updates["text"] = text_input
            
            if time_input:
                new_dt = parse(time_input, fuzzy=True)
                if new_dt.tzinfo is None:
                    user_tz = await UserSettings(self.bot).get_timezone(self.reminder.user_id)
                    new_dt = new_dt.astimezone(ZoneInfo(user_tz))
                validate_future_time(new_dt)
                updates["due"] = new_dt
            
            if updates:
                await interaction.response.defer()
            else:
                await interaction.response.send_message(
                    "No changes were made to the reminder.",
                    ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"Error updating reminder:\n{str(e)}",
                ephemeral=True
            )
