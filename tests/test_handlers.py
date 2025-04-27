# modmail-plugins/RemindMePro/tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytz

from handlers.user_commands import UserCommands
from core.models import Reminder

class TestUserCommands:
    @pytest.fixture
    def mock_commands(self):
        bot = MagicMock()
        storage = AsyncMock()
        user_settings = AsyncMock()
        return UserCommands(bot, storage, user_settings)

    @pytest.mark.asyncio
    async def test_create_reminder_success(self, mock_commands):
        """Test successful reminder creation"""
        ctx = AsyncMock()
        ctx.author.id = 123
        ctx.channel.id = 456
        mock_commands.user_settings.get_timezone.return_value = "UTC"
        
        with patch('handlers.user_commands.parse_user_time') as mock_parse:
            mock_parse.return_value = datetime.now(pytz.UTC) + timedelta(hours=1)
            await mock_commands.create_reminder(ctx, text="in 1 hour test reminder")
            
            mock_commands.storage.create_reminder.assert_awaited_once()
            ctx.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_reminder_invalid_time(self, mock_commands):
        """Test handling of invalid time input"""
        ctx = AsyncMock()
        mock_commands.user_settings.get_timezone.return_value = "UTC"
        
        with patch('handlers.user_commands.parse_user_time') as mock_parse:
            mock_parse.side_effect = ValueError("Invalid time format")
            await mock_commands.create_reminder(ctx, text="invalid time")
            
            embed = ctx.send.call_args[0][0]
            assert "Invalid" in embed.title
            assert "format" in embed.description

    @pytest.mark.asyncio
    async def test_list_reminders_empty(self, mock_commands):
        """Test listing reminders when none exist"""
        ctx = AsyncMock()
        mock_commands.storage.get_user_reminders.return_value = []
        
        await mock_commands.list_reminders(ctx)
        
        embed = ctx.send.call_args[0][0]
        assert "No reminders" in embed.title
        
