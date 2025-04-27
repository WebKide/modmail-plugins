# modmail-plugins/RemindMePro/tests/test_utilities.py
import pytest
from datetime import datetime, timedelta
import pytz

from core.utilities import parse_user_time, validate_future_time

class TestTimeUtilities:
    def test_parse_relative_time(self):
        """Test parsing relative time strings"""
        now = datetime.now(pytz.UTC)
        result = parse_user_time("in 1 hour", "UTC")
        assert result > now
        assert result <= now + timedelta(hours=1, minutes=1)

    def test_parse_absolute_time(self):
        """Test parsing absolute time strings"""
        result = parse_user_time("tomorrow at 3pm", "UTC")
        assert result.hour == 15 or result.hour == 3  # Depends on timezone

    def test_validate_future_time(self):
        """Test future time validation"""
        future = datetime.now(pytz.UTC) + timedelta(minutes=1)
        validate_future_time(future)  # Should not raise

        past = datetime.now(pytz.UTC) - timedelta(minutes=1)
        with pytest.raises(ValueError):
            validate_future_time(past)

    def test_timezone_handling(self):
        """Test timezone conversion"""
        ny_time = parse_user_time("10am", "America/New_York")
        assert ny_time.tzinfo == pytz.UTC
        utc_time = parse_user_time("10am", "UTC")
        assert ny_time.hour != utc_time.hour  # Should differ by timezone offset
