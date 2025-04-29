# modmail-plugins/remindmepro/ui/edit_reminder_modals.py
from discord.ui import Modal, InputText
import discord
from datetime import datetime
from dateutil.parser import parse

from ..corefunc.schemas import Reminder
from ..corefunc.utilities import validate_future_time

class EditReminderModal(Modal):
    """Modal for editing reminder details"""
    
    def __init__(self, reminder: Reminder):
        super().__init__(title="Edit Reminder")
        self.reminder = reminder
        self.new_time = None
        self.new_text = None
        
        self.add_item(InputText(
            label="New Reminder Text",
            placeholder="What would you like to be reminded about?",
            value=reminder.text,
            required=False,
            style=discord.InputTextStyle.long
        ))
        
        self.add_item(InputText(
            label="New Date/Time",
            placeholder="e.g. 'tomorrow at 3pm' or 'April 1'",
            value=discord.utils.format_dt(reminder.due, "f"),
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            updates = {}
            text_input = self.children[0].value.strip()
            time_input = self.children[1].value.strip()
            
            if text_input and text_input != self.reminder.text:
                updates["text"] = text_input
            
            if time_input:
                new_dt = parse(time_input, fuzzy=True)
                if new_dt.tzinfo is None:
                    new_dt = new_dt.replace(tzinfo=datetime.timezone.utc)
                validate_future_time(new_dt)
                updates["due"] = new_dt
            
            if updates:
                await interaction.response.defer()
                self.new_time = time_input
                self.new_text = text_input
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
            
