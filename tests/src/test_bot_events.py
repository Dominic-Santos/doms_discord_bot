import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from src.bot import Bot
from src.helpers import MAINTENANCE_MODE_MESSAGE
from src.pokemon import Pokemon_Event


class MockCtx():
    def __init__(self):
        self.guild = MagicMock(id=123)
        self.channel = MagicMock(id=234)

    async def respond(self, message, ephemeral=False):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return


def raise_exception():
    raise Exception("testing")


class MockEvent():
    def __init__(self, name="test event", old=True):
        self.name = name
        self.location = "hell"
        date_format = "%b %d,%Y"
        if old:
            self.start_time = datetime.strptime("Jan 14,2025", date_format)
            self.end_time = datetime.strptime("Jan 17,2025", date_format)
        else:
            mock_year = datetime.now().year + 1
            self.start_time = datetime.strptime(
                f"Jan 14,{mock_year}", date_format
            )
            self.end_time = datetime.strptime(
                f"Jan 17,{mock_year}", date_format
            )
        self.url = "www.test.com"
        self.creator_id = "im_a_bot"
        self.canceled = False

    async def cancel(self):
        self.canceled = True


class MockUpdateGuildEvent():
    def __init__(self):
        self.calls = []

    async def update(self, guild_id, events):
        self.calls.append({
            "guild_id": guild_id,
            "events": events
        })


class TestBotEvents(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_events.requests")
    @patch("src.bot_events.get_store_events")
    @patch("src.bot_events.get_premier_events")
    @patch("src.bot_events.json")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_events(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_json,
        mock_premier_events,
        mock_store_events,
        mock_requests
    ):
        mock_premier_events.return_value = [
            Pokemon_Event(
                e_name,
                "e_type",
                "e_location",
                "January 1, 2025",
                "e_logo",
                True
            )
            for e_name in ["e1", "e2", "e3"]
        ]
        mock_store_events.return_value = {
            "abc-123": [
                Pokemon_Event(
                    "event1",
                    "e_type",
                    "e_location",
                    "January 1, 2025",
                    "e_logo",
                    False
                )
            ],
            "xyz-123": [
                Pokemon_Event(
                    "event2",
                    "e_type",
                    "e_location",
                    "January 1, 2025",
                    "e_logo",
                    False
                )
            ]
        }
        mock_requests.get.return_value = MagicMock(
            status_code=200,
            content="content"
        )
        mock_logger_instance = mock_logger.return_value
        mock_json.load.return_value = {}
        mock_bot = MagicMock(user=MagicMock(id="im_a_bot"))
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
            "test event\nhell\n2025-01-14/2025-01-16"
            "\n\nwww.test.com"
        )

        assert b.event_channels == {}
        await b.set_events_channel(mock_ctx)
        assert b.event_channels.get("123", None) == 234
        assert mock_ctx.last_response == "Events channel set successfully!"

        await b.remove_events_channel(mock_ctx)
        assert b.event_channels.get("123", None) is None
        assert mock_ctx.last_response == "Events channel removed successfully!"

        guildevents = [
            MockEvent("event1"),
            MockEvent("event2", old=False),
            MockEvent("event3", old=False)
        ]
        b.event_channels["123"] = 1234
        mock_guild = MagicMock()
        mock_guild.create_scheduled_event = AsyncMock()
        send_mock = AsyncMock()
        mock_bot.get_channel.return_value = MagicMock(
            send=send_mock
        )
        mock_bot.fetch_guild = AsyncMock()
        mock_bot.fetch_guild.return_value = mock_guild
        mock_guild.fetch_scheduled_events = AsyncMock()
        mock_guild.fetch_scheduled_events.return_value = guildevents
        mock_year = datetime.now().date().year + 1
        mock_old_year = mock_year - 2
        eventlist = [
            Pokemon_Event(
                e["name"],
                e["type"],
                "hell",
                e["date"],
                "logo.png",
                False
            )
            for e in [
                {
                    "name": "e1",
                    "type": "friendly",
                    "date": f"January 14-16,{mock_year}"
                },
                {
                    "name": "e2",
                    "type": "friendly",
                    "date": f"January 20,{mock_year}"
                },
                {
                    "name": "e3",
                    "type": "friendly",
                    "date": f"January 20,{mock_old_year}"
                },
                {
                    "name": "event2",
                    "type": "friendly",
                    "date": f"January 14-16,{mock_year}"
                },
                {
                    "name": "event2",
                    "date": f"January 14-16,{mock_year}",
                    "type": "League"
                }
            ]
        ]
        b.print_event = MagicMock()
        b.print_event.return_value = "printed"
        await b.update_guild_events(123, eventlist)
        assert guildevents[0].canceled is False
        assert guildevents[1].canceled is False
        assert guildevents[2].canceled
        assert send_mock.call_count == 3

        b.event_channels = {}
        await b.update_guild_events(123, eventlist)
        assert send_mock.call_count == 3

        mock_updater = MockUpdateGuildEvent()
        b.update_guild_events = mock_updater.update

        await b.sync_events(mock_ctx)
        assert mock_ctx.last_response == "Nothing to sync"
        assert len(mock_updater.calls) == 0

        b.premier_following["123"] = True
        b.events_following["123"] = ["abc-123"]
        await b.sync_events(mock_ctx)
        assert mock_ctx.last_response == "Events synced successfully!"
        assert len(mock_updater.calls) == 1
        firstcall = mock_updater.calls[0]
        assert firstcall["guild_id"] == 123
        assert len(firstcall["events"]) == 4

        b.maintenance = True
        await b.sync_events(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        for event in guildevents:
            event.canceled = False
        b.event_channels["123"] = 1234
        await b.delete_all_events(mock_ctx)
        assert mock_ctx.last_response == "Events deleted successfully!"
        for event in guildevents:
            assert event.canceled

        send_calls = send_mock.call_count
        b.event_channels = {}
        await b.delete_all_events(mock_ctx)
        assert send_mock.call_count == send_calls

        b.premier_following = {
            "123": True,
            "234": True,
            "345": False
        }
        b.events_following = {
            "234": ["abc-123"],
            "345": ["not-found"]
        }
        mock_updater.calls = []
        await b.sync_events_task()
        assert len(mock_updater.calls) == 0

        b.maintenance = False
        await b.sync_events_task()
        assert len(mock_updater.calls) == 2
