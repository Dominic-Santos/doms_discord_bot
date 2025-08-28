import unittest
from unittest.mock import patch, MagicMock
from src.bot import Bot
from src.helpers import MAINTENANCE_MODE_MESSAGE


class MockCtx():
    def __init__(self):
        self.channel = MagicMock()
        self.channel.id = 101
        self.channel.name = "test channel"
        self.guild = MagicMock()
        self.guild.id = 202

    async def respond(self, message, ephemeral=False):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return

    async def send(self, post):
        self.last_response = post


async def mock_empty_func():
    return


class TestBotNewsfeed(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_newsfeed.json")
    @patch("builtins.open")
    async def test_bot_newsfeed(
        self,
        mock_open,
        mock_nf_json,
        mock_discord,
        mock_logger,
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_nf_json.load.side_effect = Exception("failed")

        b = Bot("faketoken", False, "123")

        mock_discord.Bot.assert_called_once()
        assert mock_open.call_count > 1
        mock_logger.assert_called_once()
        assert mock_logger_instance.warning.call_count > 1
        assert b.newsfeed_channels == {}

        b.add_tasks()
        b.run()

        mock_bot.run.assert_called_once()

        mock_nf_json.dump.side_effect = Exception("failed")
        b.save_newsfeed_channels()
        mock_logger_instance.error.assert_called_once()

        mock_ctx = MockCtx()
        b.newsfeed_channels = {}
        await b.set_newsfeed_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Newsfeed channel set to test channel!"
        )
        assert str(mock_ctx.guild.id) in b.newsfeed_channels

        b.do_get_newsfeed = mock_empty_func
        await b.get_newsfeed(mock_ctx)
        assert mock_ctx.last_response == "Newsfeed posts have been updated!"

        calls = mock_logger_instance.info.call_count
        await b.get_newsfeed_task()
        assert mock_logger_instance.info.call_count == calls + 2

        await b.disable_newsfeed(mock_ctx)
        assert mock_ctx.last_response == "Newsfeed disabled!"
        assert str(mock_ctx.guild.id) not in b.newsfeed_channels

        await b.disable_newsfeed(mock_ctx)
        assert mock_ctx.last_response == "Newsfeed already disabled!"

    @patch("src.bot_newsfeed.get_newsfeed")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_do_getnewsfeed(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_newsfeed
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", False, "123")

        mock_newsfeed.return_value = False

        await b.do_get_newsfeed()

        assert mock_logger_instance.info.call_count == 1

        mock_newsfeed.return_value = ["this is a post"]
        b.newsfeed_channels = {"1234": {"channel_id": "2345"}}
        mock_bot.get_channel.return_value = None

        warning_calls = mock_logger_instance.warning.call_count
        await b.do_get_newsfeed()
        assert mock_logger_instance.warning.call_count == warning_calls + 1

        mock_ctx = MockCtx()
        mock_bot.get_channel.return_value = mock_ctx
        await b.do_get_newsfeed()

        assert mock_ctx.last_response == "this is a post"
        assert b.newsfeed_channels["1234"]["latest_post"] == "this is a post"

        mock_ctx.last_response = "nothing"
        await b.do_get_newsfeed()
        assert mock_ctx.last_response == "nothing"

    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_newsfeed_maintenance(
        self,
        mock_open,
        mock_discord,
        mock_logger,
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", True, "123")

        mock_ctx = MockCtx()
        await b.get_newsfeed(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.get_newsfeed_task()
        assert mock_logger_instance.info.call_count == 2
