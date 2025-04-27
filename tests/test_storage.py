# modmail-plugins/RemindMePro/tests/test_storage.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import pytz
from bson import ObjectId

from core.storage import ReminderStorage
from core.models import Reminder

class TestReminderStorage:
    @pytest.fixture
    def mock_storage(self):
        collection = AsyncMock()
        return ReminderStorage(collection)

    @pytest.mark.asyncio
    async def test_create_reminder(self, mock_storage):
        """Test creating a new reminder"""
        reminder = Reminder(
            user_id=123,
            text="Test",
            due=datetime.now(pytz.UTC) + timedelta(hours=1)
        )
        mock_storage.collection.insert_one.return_value.inserted_id = ObjectId()
        
        reminder_id = await mock_storage.create_reminder(reminder)
        assert isinstance(reminder_id, str)
        
        mock_storage.collection.insert_one.assert_awaited_once_with(
            reminder.dict()
        )

    @pytest.mark.asyncio
    async def test_get_user_reminders(self, mock_storage):
        """Test retrieving user reminders"""
        mock_reminder = {
            "user_id": 123,
            "text": "Test",
            "due": datetime.now(pytz.UTC),
            "status": "active"
        }
        mock_storage.collection.find.return_value.to_list.return_value = [mock_reminder]
        
        reminders = await mock_storage.get_user_reminders(123)
        assert len(reminders) == 1
        assert isinstance(reminders[0], Reminder)

    @pytest.mark.asyncio
    async def test_mark_completed(self, mock_storage):
        """Test marking reminder as completed"""
        test_id = str(ObjectId())
        mock_storage.collection.update_one.return_value.modified_count = 1
        
        result = await mock_storage.mark_completed(test_id)
        assert result is True
        
        mock_storage.collection.update_one.assert_awaited_once()
        
