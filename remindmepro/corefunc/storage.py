# modmail-plugins/remindmepro/corefunc/storage.py
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import pytz
from discord.ext.commands import Bot

from .schemas import Reminder

log = logging.getLogger("Modmail")

class ReminderStorage:
    """Handles all database operations for reminders"""
    
    def __init__(self, bot: Bot):
        self.db = bot.plugin_db.get_partition(self)

    async def get_user_reminders(self, user_id: int, limit: int = 50) -> List[Reminder]:
        """Get active reminders for a user, sorted by due date"""
        try:
            cursor = self.db.find({
                "user_id": user_id,
                "status": "active"
            })
            reminders = await cursor.to_list(length=limit)
            # Manual sorting since we can't chain .sort()
            reminders.sort(key=lambda x: x["due"])
            return [Reminder(**doc) for doc in reminders]
        except Exception as e:
            log.error(f"Error getting reminders for user {user_id}: {str(e)}")
            return []

    async def get_due_reminders(self, batch_size: int = 100) -> List[Reminder]:
        """Get reminders that are due, for batch processing"""
        try:
            cursor = self.db.find({
                "due": {"$lte": datetime.now(pytz.UTC)},
                "status": "active"
            })
            reminders = await cursor.to_list(length=batch_size)
            return [Reminder(**doc) for doc in reminders]
        except Exception as e:
            log.error(f"Error getting due reminders: {str(e)}")
            return []

    async def create_reminder(self, reminder: Reminder) -> str:
        """Insert a new reminder and return its ID"""
        try:
            data = reminder.dict()
            # Create a composite ID since we don't have ObjectId
            reminder_id = f"{data['user_id']}_{int(data['due'].timestamp())}"
            data["_id"] = reminder_id
            await self.db.insert_one(data)
            return reminder_id
        except Exception as e:
            log.error(f"Error creating reminder: {str(e)}")
            raise

    async def update_reminder(self, reminder_id: str, update_data: dict) -> bool:
        """Update a reminder by ID"""
        try:
            result = await self.db.update_one(
                {"_id": reminder_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            log.error(f"Error updating reminder {reminder_id}: {str(e)}")
            return False

    async def mark_completed(self, reminder_id: str) -> bool:
        """Mark a reminder as completed instead of deleting"""
        return await self.update_reminder(reminder_id, {
            "status": "completed",
            "completed_at": datetime.now(pytz.UTC)
        })

    async def cleanup_old_reminders(self, days: int = 30):
        """Remove completed reminders older than X days"""
        cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
        await self.db.delete_many({
            "status": "completed",
            "completed_at": {"$lte": cutoff}
        })
    
    async def check_reminder_conflict(self, user_id: int, due: datetime) -> Optional[Reminder]:
        """Check if user already has a reminder at similar time"""
        window_start = due - timedelta(minutes=5)
        window_end = due + timedelta(minutes=5)
        doc = await self.db.find_one({
            "user_id": user_id,
            "due": {"$gte": window_start, "$lte": window_end},
            "status": "active"
        })
        return Reminder(**doc) if doc else None
