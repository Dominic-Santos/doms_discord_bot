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

 
class TestBotLegalCards(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_legalcards.get_legal_cards")
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
        mock_legal_cards
    ):
        mock_load.return_value = ({}, {})
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
        
        assert mock_logger_instance.info.call_count == 2

        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == 5

        mock_ctx = MockCtx()
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == "Legal cards list has been updated!"
