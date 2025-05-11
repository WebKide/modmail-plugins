# modmail-plugins/remindmepro/corefunc/utilities.py
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from parsedatetime import Calendar
import pytz

SUPPORTED_LOCATIONS_URL = "https://gist.github.com/mjrulesamrat/0c1f7de951d3c508fb3a20b4b0b33a98"

def parse_user_time(time_str: str, user_tz: str) -> datetime:
    """
    Parse user-provided time string into timezone-aware datetime
    Handles both relative (in 5 minutes) and absolute (at 3pm) formats
    """
    user_timezone = pytz.timezone(user_tz)
    now = datetime.now(user_timezone)
    
    try:
        # Try parsing as relative time first
        if time_str.lower().startswith("in "):
            cal = Calendar()
            time_struct, parse_status = cal.parse(time_str[3:])
            if not parse_status:
                raise ValueError("Invalid time format. Use like 'in 2 hours' or 'in 30m'")
            delta = datetime(*time_struct[:6]) - now  # More precise parsing
            return (datetime.now(pytz.UTC) + delta).astimezone(pytz.UTC)
        
        # Try parsing as absolute time
        dt = parse(time_str, fuzzy=True, default=now)
        if dt.tzinfo is None:
            dt = user_timezone.localize(dt)
        return dt.astimezone(pytz.UTC)
    
    except Exception as e:
        raise ValueError(f"Could not parse time: {str(e)}")

def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string"""
    from discord.utils import format_dt
    return format_dt(dt, "R")

def validate_future_time(dt: datetime) -> None:
    """Validate that datetime is in the future"""
    if dt <= datetime.now(pytz.UTC):
        raise ValueError("Time must be in the future")

def calculate_next_occurrence(dt: datetime, frequency: str) -> datetime:
    """Calculate next occurrence for recurring reminders"""
    if frequency == "daily":
        return dt + relativedelta(days=1)
    elif frequency == "weekly":
        return dt + relativedelta(weeks=1)
    raise ValueError(f"Unsupported frequency: {frequency}")
