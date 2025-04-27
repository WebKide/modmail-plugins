# modmail-plugins/RemindMePro/tests/test_models.py
import pytest
from datetime import datetime, timedelta
import pytz
from bson import ObjectId

from core.models import Reminder

class TestReminderModel:
    def test_valid_reminder_creation(self):
        """Test creating a valid reminder"""
        reminder = Reminder(
            user_id=123,
            text="Test reminder",
            due=datetime.now(pytz.UTC) + timedelta(hours=1)
        )
        assert reminder.user_id == 123
        assert reminder.text == "Test reminder"
        assert reminder.status == "active"

    def test_text_sanitization(self):
        """Test text sanitization logic"""
        # Test with special characters
        reminder = Reminder(
            user_id=123,
            text="Test <script>alert('xss')</script> reminder",
            due=datetime.now(pytz.UTC) + timedelta(hours=1)
        )
        assert "script" not in reminder.text
        assert "␀" in reminder.text

        # Test with multiple dashes
        reminder = Reminder(
            user_id=123,
            text="Test ---reminder---with---dashes---",
            due=datetime.now(pytz.UTC) + timedelta(hours=1)
        )
        assert "---" not in reminder.text
        assert "--reminder--with--dashes--" in reminder.text

    def test_timezone_validation(self):
        """Test timezone validation"""
        # Valid timezone
        reminder = Reminder(
            user_id=123,
            text="Test",
            due=datetime.now(pytz.UTC) + timedelta(hours=1),
            timezone="America/New_York"
        )
        assert reminder.timezone == "America/New_York"

        # Invalid timezone
        with pytest.raises(ValueError):
            Reminder(
                user_id=123,
                text="Test",
                due=datetime.now(pytz.UTC) + timedelta(hours=1),
                timezone="Invalid/Timezone"
            )

    def test_future_time_validation(self):
        """Test that due date must be in the future"""
        with pytest.raises(ValueError):
            Reminder(
                user_id=123,
                text="Test",
                due=datetime.now(pytz.UTC) - timedelta(hours=1)
            )
            
