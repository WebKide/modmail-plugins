# modmail-plugins/RemindMePro/ui/views.py
from discord.ui import View, Button
import discord
from typing import Optional

from core.models import Reminder
from core.storage import ReminderStorage

class ReminderControlsView(View):
    """View for managing individual reminders"""
    
    def __init__(self, storage: ReminderStorage, reminder: Reminder, is_admin: bool = False):
        super().__init__(timeout=180)
        self.storage = storage
        self.reminder = reminder
        self.is_admin = is_admin
        self.add_buttons()

    def add_buttons(self):
        """Add appropriate buttons based on reminder state"""
        self.clear_items()
        
        # Basic controls
        self.add_item(Button(
            emoji="⏸️" if self.reminder.status == "active" else "▶️",
            style=discord.ButtonStyle.grey,
            custom_id="toggle_pause"
        ))
        
        self.add_item(Button(
            emoji="✏️",
            style=discord.ButtonStyle.grey,
            custom_id="edit_reminder"
        ))
        
        # Recurring controls
        if not self.reminder.recurring:
            self.add_item(Button(
                emoji="🔁",
                style=discord.ButtonStyle.green,
                custom_id="set_recurring"
            ))
        else:
            self.add_item(Button(
                emoji="❌",
                label="Stop Recurring",
                style=discord.ButtonStyle.red,
                custom_id="stop_recurring"
            ))
        
        # Delete button
        self.add_item(Button(
            emoji="🗑️",
            style=discord.ButtonStyle.red,
            custom_id="delete_reminder"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verify user has permission to interact"""
        if interaction.user.guild_permissions.manage_messages:
            return True
        if interaction.user.id == self.reminder.user_id:
            return True
        if self.is_admin:
            return True
            
        await interaction.response.send_message(
            "You don't have permission to modify this reminder.",
            ephemeral=True
        )
        return False

    async def handle_interaction(self, interaction: discord.Interaction, custom_id: str):
        """Central handler for all button interactions"""
        try:
            if custom_id == "toggle_pause":
                new_status = "paused" if self.reminder.status == "active" else "active"
                await self.storage.update_reminder(
                    str(self.reminder.id),
                    {"status": new_status}
                )
                await interaction.response.send_message(
                    f"Reminder {'paused' if new_status == 'paused' else 'resumed'}.",
                    ephemeral=True
                )
            
            elif custom_id == "edit_reminder":
                modal = EditReminderModal(self.reminder)
                await interaction.response.send_modal(modal)
                await modal.wait()
                
                if modal.new_time or modal.new_text:
                    await interaction.followup.send(
                        "Reminder updated successfully!",
                        ephemeral=True
                    )
            
            # Other handlers would go here...
            
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to update reminder: {str(e)}",
                ephemeral=True
            )
            
