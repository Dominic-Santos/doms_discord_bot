import unittest
from unittest.mock import patch, MagicMock
from src.bot import Bot

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

    @patch("src.bot.tasks")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_newsfeed.json")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_newsfeed(
        self,
        mock_load,
        mock_open,
        mock_dl_json,
        mock_nf_json,
        mock_discord,
        mock_logger,
        mock_tasks
    ):
        mock_load.return_value = ({}, {}, {})
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        def raise_exception():
            raise Exception("test error")
        try:
            raise_exception()
        except Exception as e:
            assert str(e) == "test error"

        mock_nf_json.load = raise_exception

        b = Bot("faketoken")

        mock_dl_json.load.assert_called_once()
        
        mock_discord.Bot.assert_called_once()
        assert mock_open.call_count == 2
        mock_logger.assert_called_once()
        assert mock_logger_instance.info.call_count == 1
        assert b.newsfeed_channels == {}

        b.add_tasks()
        b.run()

        mock_bot.run.assert_called_once()

        mock_nf_json.dump = raise_exception
        b.save_newsfeed_channels()
        mock_logger_instance.error.assert_called_once()

        mock_ctx = MockCtx()
        await b.set_newsfeed_channel(mock_ctx)
        assert mock_ctx.last_response == "Newsfeed channel set to test channel!"

        b.do_get_newsfeed = mock_empty_func
        await b.get_newsfeed(mock_ctx)
        assert mock_ctx.last_response == "Newsfeed posts have been updated!"

        await b.get_newsfeed_task()
        assert mock_logger_instance.info.call_count == 4

    
    @patch("src.bot_newsfeed.get_newsfeed")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_newsfeed.json")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_do_getnewsfeed(
        self,
        mock_load,
        mock_open,
        mock_dl_json,
        mock_nf_json,
        mock_discord,
        mock_logger,
        mock_newsfeed
    ):
        mock_load.return_value = ({}, {}, {})
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        def raise_exception():
            raise Exception("test error")
        try:
            raise_exception()
        except Exception as e:
            assert str(e) == "test error"

        mock_nf_json.load = raise_exception

        b = Bot("faketoken")

        mock_newsfeed.return_value = False

        await b.do_get_newsfeed()

        assert mock_logger_instance.info.call_count == 2

        mock_newsfeed.return_value = ["this is a post"]
        b.newsfeed_channels = {"1234": {"channel_id": "2345"}}
        mock_bot.get_channel.return_value = None

        await b.do_get_newsfeed()
        mock_logger_instance.warning.assert_called_once()


        mock_ctx = MockCtx()
        mock_bot.get_channel.return_value = mock_ctx
        await b.do_get_newsfeed()

        assert mock_ctx.last_response == "this is a post"
        assert b.newsfeed_channels["1234"]["latest_post"] == "this is a post"

        mock_ctx.last_response = "nothing"
        await b.do_get_newsfeed()
        assert mock_ctx.last_response == "nothing"

