# modmail-plugins/RemindMePro/core/user_settings.py
from typing import Dict
import pytz
from motor.motor_asyncio import AsyncIOMotorCollection

class UserSettings:
    """Manages user-specific settings like timezones"""
    
    def __init__(self, db_collection: AsyncIOMotorCollection):
        self.db = db_collection
        self._timezone_cache: Dict[int, str] = {}

    async def load_timezones(self):
        """Load all user timezones into cache"""
        self._timezone_cache.clear()
        async for user in self.db.find({"timezone": {"$exists": True}}):
            self._timezone_cache[user["user_id"]] = user["timezone"]

    async def get_timezone(self, user_id: int) -> str:
        """Get user's timezone with cache fallback"""
        if user_id in self._timezone_cache:
            return self._timezone_cache[user_id]
        
        user = await self.db.find_one({"user_id": user_id})
        if user and "timezone" in user:
            self._timezone_cache[user_id] = user["timezone"]
            return user["timezone"]
        
        return "UTC"

    async def set_timezone(self, user_id: int, timezone: str) -> None:
        """Set user's timezone with validation"""
        if timezone not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone. See supported locations:\n{SUPPORTED_LOCATIONS_URL}")
        
        await self.db.update_one(
            {"user_id": user_id},
            {"$set": {"timezone": timezone}},
            upsert=True
        )
        self._timezone_cache[user_id] = timezone
        
