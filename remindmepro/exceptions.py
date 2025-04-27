# modmail-plugins/RemindMePro/exceptions.py
class ReminderError(Exception):
    """Base exception for reminder-related errors"""
    pass

class InvalidTimezoneError(ReminderError):
    """Raised when an invalid timezone is provided"""
    def __init__(self, timezone):
        super().__init__(f"Invalid timezone: {timezone}")

class TimeParseError(ReminderError):
    """Raised when time parsing fails"""
    pass

class ReminderNotFoundError(ReminderError):
    """Raised when a reminder cannot be found"""
    pass

class PermissionError(ReminderError):
    """Raised when user lacks permission for an operation"""
    pass

class RateLimitError(ReminderError):
    """Raised when rate limits are exceeded"""
    pass
    
