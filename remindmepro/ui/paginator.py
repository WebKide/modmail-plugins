# modmail-plugins/RemindMePro/ui/paginator.py
from discord.ui import View, Button
import discord
from typing import List

from .core.models import Reminder
from .core.storage import ReminderStorage

class ReminderPaginator(View):
    """Custom paginator with enhanced controls for reminders"""
    
    def __init__(self, bot, embeds: List[discord.Embed], storage: ReminderStorage, 
                 user_id: int = None, is_admin: bool = False):
        super().__init__(timeout=120)
        self.bot = bot
        self.embeds = embeds
        self.current_page = 0
        self.storage = storage
        self.user_id = user_id
        self.is_admin = is_admin
        self.message = None
        self.update_buttons()

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

    def update_buttons(self):
        self.clear_items()
        
        # Page navigation
        if len(self.embeds) > 1:
            self.add_item(Button(emoji="⬅️", style=discord.ButtonStyle.blurple, 
                               disabled=self.current_page == 0, row=0))
            self.add_item(Button(emoji="➡️", style=discord.ButtonStyle.blurple,
                               disabled=self.current_page == len(self.embeds) - 1, row=0))
        
        # Action buttons
        action_row = 1
        if self.user_id:
            self.add_item(Button(emoji="✏️", style=discord.ButtonStyle.grey, 
                               custom_id="edit_reminder", row=action_row))
            self.add_item(Button(emoji="🗑️", style=discord.ButtonStyle.red, 
                               custom_id="delete_reminder", row=action_row))
        
        if hasattr(self, 'is_active_reminder') and self.is_active_reminder:
            self.add_item(Button(emoji="⏸️", style=discord.ButtonStyle.grey, 
                               custom_id="pause_reminder", row=action_row))
            self.add_item(Button(emoji="🔁", style=discord.ButtonStyle.green, 
                               custom_id="set_recurring", row=action_row))
        
        self.add_item(Button(emoji="❎", style=discord.ButtonStyle.grey, 
                           custom_id="close_message", row=action_row))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only authorized users can interact"""
        if interaction.user.guild_permissions.manage_messages:
            return True
        if self.user_id and interaction.user.id == self.user_id:
            return True
        if self.is_admin:
            return True
        
        await interaction.response.send_message(
            "You don't have permission to interact with this reminder.", 
            ephemeral=True
        )
        return False

    async def get_current_reminder(self) -> Optional[Reminder]:
        """Extract reminder from current embed footer"""
        try:
            if not self.embeds or self.current_page >= len(self.embeds):
                return None
                
            embed = self.embeds[self.current_page]
            if not embed.footer or not embed.footer.text.startswith('Reminder ID: '):
                return None
                
            reminder_id = embed.footer.text[13:]
            if not reminder_id.strip():
                return None
                
            return await self.storage.get_reminder(reminder_id)
            
        except Exception as e:
            log.error(f"Error getting current reminder: {str(e)}", exc_info=True)
            return None
