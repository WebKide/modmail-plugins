# modmail-plugins/RemindMePro/core/time.py
from datetime import datetime
from typing import Optional, Union
import pytz
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from discord.ext.commands import BadArgument

class UserFriendlyTime:
    """A converter that handles human-style time inputs with timezone support"""
    
    def __init__(self, converter=None, *, default=None, timezone="UTC"):
        self.converter = converter
        self.default = default
        self.timezone = pytz.timezone(timezone)

    async def convert(self, ctx, argument):
        """Parse user input into timezone-aware datetime"""
        try:
            # Get user's timezone if available
            if hasattr(ctx.cog, 'user_settings'):
                user_tz = await ctx.cog.user_settings.get_timezone(ctx.author.id)
            else:
                user_tz = "UTC"
                
            tz = pytz.timezone(user_tz)
            now = datetime.now(tz)
            
            # Try to parse as relative time first
            if argument.lower().startswith("in "):
                time_part = argument[3:]
                try:
                    delta = parse(time_part, fuzzy=True, default=now) - now
                    dt = datetime.now(pytz.UTC) + delta
                    remaining = ""
                except:
                    raise BadArgument("Couldn't parse relative time")
            else:
                # Parse absolute time
                dt, tokens = parse(argument, fuzzy_with_tokens=True, default=now)
                remaining = " ".join(tokens).strip()
                if dt.tzinfo is None:
                    dt = tz.localize(dt)
                dt = dt.astimezone(pytz.UTC)

            # Validate the time is in the future
            if dt <= datetime.now(pytz.UTC):
                raise BadArgument("Reminder time must be in the future")

            return self.__class__._parse_result(dt, remaining)
            
        except Exception as e:
            raise BadArgument(f"Could not parse time: {str(e)}")

    @staticmethod
    def _parse_result(dt, remaining):
        if not remaining:
            remaining = None
        return dt, remaining
        
