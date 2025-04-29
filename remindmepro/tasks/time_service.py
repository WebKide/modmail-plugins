# modmail-plugins/remindmepro/tasks/time_service.py
from datetime import datetime, timedelta
from typing import Optional, Literal
import pytz
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from ..corefunc.models import Reminder

class TimeService:
    """Service for time-related operations"""
    
    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = pytz.timezone(default_timezone)

    def parse_time_input(self, time_str: str, user_tz: str) -> datetime:
        """Parse user input into timezone-aware datetime"""
        user_timezone = pytz.timezone(user_tz)
        now = datetime.now(user_timezone)
        
        try:
            # Relative time (in 5 minutes)
            if time_str.lower().startswith("in "):
                delta = parse(time_str[3:], fuzzy=True, default=now) - now
                return (datetime.now(pytz.UTC) + delta).astimezone(pytz.UTC)
            
            # Absolute time (at 3pm)
            dt = parse(time_str, fuzzy=True, default=now)
            if dt.tzinfo is None:
                dt = user_timezone.localize(dt)
            return dt.astimezone(pytz.UTC)
            
        except Exception as e:
            raise ValueError(f"Could not parse time: {str(e)}")

    def validate_future_time(self, dt: datetime) -> None:
        """Ensure datetime is in the future"""
        if dt <= datetime.now(pytz.UTC):
            raise ValueError("Time must be in the future")

    def calculate_next_occurrence(
        self, 
        dt: datetime, 
        frequency: Literal["daily", "weekly"]
    ) -> datetime:
        """Calculate next occurrence for recurring reminders"""
        if frequency == "daily":
            return dt + timedelta(days=1)
        elif frequency == "weekly":
            return dt + timedelta(weeks=1)
        raise ValueError(f"Unsupported frequency: {frequency}")

    def format_relative_time(self, dt: datetime) -> str:
        """Format datetime as relative time string"""
        from discord.utils import format_dt
        return format_dt(dt, "R")

    def format_datetime(
        self, 
        dt: datetime, 
        include_relative: bool = True
    ) -> str:
        """Format datetime for display"""
        from discord.utils import format_dt
        formatted = format_dt(dt, "f")
        if include_relative:
            formatted += f" ({self.format_relative_time(dt)})"
        return formatted

    def get_timezone_choices(self, search: Optional[str] = None) -> List[str]:
        """Get list of timezone choices, optionally filtered"""
        all_zones = pytz.all_timezones
        if search:
            return [zone for zone in all_zones if search.lower() in zone.lower()]
        return all_zones
        
