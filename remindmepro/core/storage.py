# modmail-plugins/RemindMePro/core/storage.py
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import pytz
import logging
from motor.motor_asyncio import AsyncIOMotorCollection

from core.models import Reminder

log = logging.getLogger(__name__)

class ReminderStorage:
    """Handles all database operations for reminders"""
    
    def __init__(self, db_collection: AsyncIOMotorCollection):
        self.collection = db_collection

    async def setup_indexes(self):
        """Create necessary database indexes"""
        await self.collection.create_index("due")
        await self.collection.create_index("user_id")
        await self.collection.create_index([("user_id", 1), ("due", 1)])
        await self.collection.create_index("status")

    async def create_reminder(self, reminder: Reminder) -> str:
        """Insert a new reminder and return its ID"""
        result = await self.collection.insert_one(reminder.dict())
        return str(result.inserted_id)

    async def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Get a single reminder by its ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(reminder_id)})
            return Reminder(**doc) if doc else None
        except Exception as e:
            log.error(f"Error fetching reminder {reminder_id}: {str(e)}")
            return None

    async def get_user_reminders(self, user_id: int, limit: int = 50) -> List[Reminder]:
        """Get active reminders for a user, sorted by due date"""
        cursor = self.collection.find({
            "user_id": user_id,
            "status": "active"
        }).sort("due", 1).limit(limit)
        return [Reminder(**doc) async for doc in cursor]

    async def get_due_reminders(self, batch_size: int = 100) -> List[Reminder]:
        """Get reminders that are due, for batch processing"""
        cursor = self.collection.find({
            "due": {"$lte": datetime.now(pytz.UTC)},
            "status": "active"
        }).limit(batch_size)
        return [Reminder(**doc) async for doc in cursor]

    async def update_reminder(self, reminder_id: str, update_data: dict) -> bool:
        """Update a reminder by ID"""
        result = await self.collection.update_one(
            {"_id": ObjectId(reminder_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def mark_completed(self, reminder_id: str) -> bool:
        """Mark a reminder as completed instead of deleting"""
        return await self.update_reminder(reminder_id, {
            "status": "completed",
            "completed_at": datetime.now(pytz.UTC)
        })

    async def cleanup_old_reminders(self, days: int = 30):
        """Remove completed reminders older than X days"""
        cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
        await self.collection.delete_many({
            "status": "completed",
            "completed_at": {"$lte": cutoff}
        })
    
