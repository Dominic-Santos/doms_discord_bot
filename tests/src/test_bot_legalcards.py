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


class TestBotLegalCards(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_legalcards.get_legal_cards")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_legal_cards(
        self,
        mock_load,
        mock_open,
        mock_discord,
        mock_logger,
        mock_legal_cards
    ):
        mock_load.return_value = ({}, {})
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", False, "123")

        inf_calls = mock_logger_instance.info.call_count
        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == inf_calls + 2

        mock_ctx = MockCtx()
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == "Legal cards list has been updated!"

        def return_error():
            return Exception("test error")

        inf_calls = mock_logger_instance.info.call_count
        err_calls = mock_logger_instance.error.call_count
        b.do_get_legal_cards = return_error
        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == inf_calls + 1
        assert mock_logger_instance.error.call_count == err_calls + 1

        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == (
            "Legal cards update failed! test error"
        )

    @patch("src.bot_legalcards.get_legal_cards")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_legal_cards_maintenance(
        self,
        mock_load,
        mock_open,
        mock_discord,
        mock_logger,
        mock_legal_cards
    ):
        mock_load.return_value = ({}, {})
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", True, "123")

        assert mock_legal_cards.call_count == 0

        inf_calls = mock_logger_instance.info.call_count
        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == inf_calls + 2
        assert mock_legal_cards.call_count == 0

        mock_ctx = MockCtx()
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE
