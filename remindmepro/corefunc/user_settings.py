# modmail-plugins/remindmepro/corefunc/user_settings.py
from typing import Dict
import pytz
from discord.ext.commands import Bot

SUPPORTED_LOCATIONS_URL = "https://gist.github.com/mjrulesamrat/0c1f7de951d3c508fb3a20b4b0b33a98"

class UserSettings:
    """Manages user-specific settings like timezones"""
    
    def __init__(self, bot: Bot):
        self.db = bot.plugin_db.get_partition(self)
        self._timezone_cache: Dict[int, str] = {}

    async def load_timezones(self):
        """Load all user timezones into cache using Modmail's plugin_db"""
        self._timezone_cache.clear()
        # Modmail's plugin_db requires using find_many instead of find
        users = await self.db.find_many({"timezone": {"$exists": True}})
        for user in users:
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
    
