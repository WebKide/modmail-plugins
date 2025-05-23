# modmail-plugins/remindmepro/corefunc/schemas.py
from pydantic import BaseModel, Field, validator
import pytz
import re
from typing import Optional, Literal
from datetime import datetime

class Reminder(BaseModel):
    """Data model for reminder objects"""
    user_id: int
    channel_id: Optional[int] = None
    text: str = Field(..., max_length=400)
    due: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    recurring: Optional[Literal["daily", "weekly"]] = None
    timezone: str = "UTC"
    status: Literal["active", "completed", "paused"] = "active"
    undelivered: bool = False

    @validator('text', allow_reuse=True)
    def sanitize_text(cls, v):
        sanitized = re.sub(r'[^\p{L}\p{N}\s.,!?\-@#\U0001F300-\U0001F6FF]', '␀', v)
        return re.sub(r'-{3,}', '--', sanitized).strip()

    @validator('timezone', allow_reuse=True)
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone. Must be one of: {pytz.all_timezones}")
        return v

    @validator('due', allow_reuse=True)
    def validate_due_future(cls, v):
        if v <= datetime.now(pytz.UTC):
            raise ValueError('Due time must be in future')
        return v

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        arbitrary_types_allowed = True
        extra = "forbid"