# remindertimezone.py
import pytz
from datetime import datetime
from typing import Dict, Optional, Set
import re
import logging

from discord.ext import commands


log = logging.getLogger("Modmail")

# Timezone validation regex
UTC_OFFSET_PATTERN = re.compile(r'^UTC([+-])(\d{1,2})$', re.IGNORECASE)

class ReminderTimezone:
    """Centralized timezone management for reminders"""

    def __init__(self, db_partition):
        self.db = db_partition
        self.user_timezones: Dict[int, pytz.BaseTzInfo] = {}

    async def get_user_timezone(self, user_id: int) -> pytz.BaseTzInfo:
        """Get cached timezone or fetch from DB"""
        if user_id in self.user_timezones:
            return self.user_timezones[user_id]

        try:
            user_data = await self.db.find_one({"_id": f"timezone_{user_id}"})
            if user_data:
                tz = pytz.FixedOffset(user_data["offset_minutes"])
                self.user_timezones[user_id] = tz
                return tz
        except Exception as e:
            log.error(f"Failed to fetch timezone for user {user_id}: {e}")

        # Default to UTC if not set or error
        return pytz.UTC

    async def set_user_timezone(self, user_id: int, timezone_str: str) -> Optional[pytz.BaseTzInfo]:
        """Validate and set user's timezone"""
        try:
            # Parse UTC offset format
            match = UTC_OFFSET_PATTERN.match(timezone_str.strip())
            if not match:
                return None

            sign, hours = match.groups()
            hours = int(hours)

            if hours > 14 or hours < -12:
                return None

            # Create fixed offset timezone
            offset_minutes = hours * 60
            if sign == '-':
                offset_minutes = -offset_minutes

            timezone = pytz.FixedOffset(offset_minutes)

            # Atomic database update
            await self.db.update_one(
                {"_id": f"timezone_{user_id}"},
                {"$set": {"offset_minutes": offset_minutes}},
                upsert=True
            )

            # Update cache
            self.user_timezones[user_id] = timezone
            return timezone

        except Exception as e:
            log.error(f"Failed to set timezone for user {user_id}: {e}")
            return None

    def clean_cache(self, active_user_ids: Set[int]):
        """Remove cached timezones for inactive users"""
        inactive_users = set(self.user_timezones.keys()) - active_user_ids
        for user_id in inactive_users:
            del self.user_timezones[user_id]

    async def format_time_with_timezone(self, dt: datetime, user_id: int) -> str:
        """Format time for display in user's timezone"""
        try:
            user_tz = await self.get_user_timezone(user_id)
            # Ensure dt is timezone-aware (UTC)
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            else:
                dt = dt.astimezone(pytz.UTC)

            local_dt = dt.astimezone(user_tz)
            return (
                f"{local_dt.strftime('%d %B %Y %H:%M %Z')}\n"
                f"({local_dt.strftime('%A')} - {local_dt.strftime('%H:%M')})"
            )
        except Exception as e:
            log.error(f"Failed to format time for user {user_id}: {e}")
            return dt.strftime('%d %B %Y %H:%M UTC')

    def get_timezone_display(self, timezone: pytz.BaseTzInfo) -> str:
        """Get human-readable timezone display"""
        if isinstance(timezone, pytz._FixedOffset):  # Check if it's a FixedOffset timezone
            offset_minutes = timezone._offset.seconds // 60
            hours = offset_minutes // 60
            # Handle UTC±0 case
            if hours == 0:
                return "UTC±0"
            # Format with proper sign
            sign = '-' if offset_minutes < 0 else '+'
            abs_hours = abs(hours)
            return f"UTC{sign}{abs_hours}"
        elif isinstance(timezone, pytz.tzinfo.BaseTzInfo):  # For named timezones
            return str(timezone)
        return "UTC"  # Fallback

class TimezoneConverter(commands.Converter):
    async def convert(self, ctx, argument):
        """Convert string to timezone with enhanced validation"""
        argument = argument.strip()
        match = UTC_OFFSET_PATTERN.match(argument)

        if not match:
            raise commands.BadArgument(
                "Invalid timezone format. Use `UTC±HH` (e.g., `UTC+2`, `UTC-5`)\n"
                "Examples: `UTC+0`, `UTC+5`, `UTC-3`, `UTC+10`"
            )

        sign, hours = match.groups()
        try:
            hours = int(hours)
            if hours > 14 or hours < 0:
                raise commands.BadArgument(
                    "Timezone offset must be between UTC+0 and UTC+14 or UTC-0 to UTC-12"
                )

            # Create a fixed offset timezone
            offset_minutes = hours * 60
            if sign == '-':
                if hours > 12:
                    raise commands.BadArgument("Negative timezone offset cannot exceed UTC-12")
                offset_minutes = -offset_minutes

            return pytz.FixedOffset(offset_minutes)

        except ValueError:
            raise commands.BadArgument(
                "Invalid timezone format. Hours must be a number.\n"
                "Use `UTC±HH` (e.g., `UTC+2`, `UTC-5`)"
            )