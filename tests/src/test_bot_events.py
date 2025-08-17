import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.bot import Bot


class MockCtx():
    def __init__(self):
        self.guild = MagicMock(
            id=123
        )

    async def respond(self, message, ephemeral=False):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return


def raise_exception():
    raise Exception("testing")


class MockEvent():
    def __init__(self):
        self.name = "test event"
        self.location = "hell"
        date_format = "%b %d,%Y"
        self.start_time = datetime.strptime("Jan 14,2025", date_format)
        self.end_time = datetime.strptime("Jan 16,2025", date_format)
        self.url = "www.test.com"


class TestBotEvents(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_events.json")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_events(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_json
    ):
        mock_logger_instance = mock_logger.return_value
        mock_json.load.return_value = {}
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        try:
            raise_exception()
        except Exception as e:
            assert str(e) == "testing"

        b = Bot("faketoken", False, "123")
        mock_json.load.assert_called_once()

        b.save_events_data()
        mock_json.dump.assert_called_once()

        mock_json.dump = raise_exception
        b.save_events_data()
        mock_logger_instance.error.assert_called_once()

        assert b.premier_following == {}
        mock_ctx = MockCtx()
        await b.unfollow_premier_events(mock_ctx)
        assert b.premier_following.get("123", None) is False
        assert mock_ctx.last_response == "Not following premier events!"

        await b.unfollow_events(mock_ctx, "abc-123")
        assert mock_ctx.last_response == "Not following abc-123"
        b.events_following = {}

        await b.follow_premier_events(mock_ctx)
        assert b.premier_following.get("123", False)
        assert mock_ctx.last_response == "Following premier events!"

        await b.follow_events(mock_ctx, "abc-123")
        assert mock_ctx.last_response == "Following events from abc-123"
        await b.follow_events(mock_ctx, "abc-123")
        assert mock_ctx.last_response == "Already following abc-123"
        await b.follow_events(mock_ctx, "abc-123-abc")
        assert mock_ctx.last_response == "Following events from abc-123-abc"

        assert len(b.events_following.get("123", [])) == 2

        await b.unfollow_events(mock_ctx, "abc-123")
        assert mock_ctx.last_response == (
            "Stopped following events from abc-123"
        )
        await b.unfollow_events(mock_ctx, "abc-123")
        assert mock_ctx.last_response == "Not following abc-123"

        assert len(b.events_following.get("123", [])) == 1

        await b.unfollow_all_events(mock_ctx)
        assert mock_ctx.last_response == "Stopped following all events"
        assert b.premier_following.get("123", None) is False
        assert b.events_following.get("123", []) == []

        mock_event = MockEvent()
        event_text = b.print_event(mock_event)
        assert event_text == (
            "test event\nhell\n2025-01-14/2025-01-15"
            "\n\nwww.test.com"
        )
