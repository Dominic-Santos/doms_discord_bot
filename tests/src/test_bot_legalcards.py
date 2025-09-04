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

    @patch("src.bot_legalcards.json.dump")
    @patch("src.bot_legalcards.get_pokemon_sets")
    @patch("src.bot_legalcards.get_banned_cards")
    @patch("src.bot_legalcards.load_card_database")
    @patch("src.bot_legalcards.get_legal_cards")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_legal_cards(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_legal_cards,
        mock_load,
        mock_banned_cards,
        mock_sets,
        mock_json_dump
    ):
        mock_load.return_value = ({}, {}, {})
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_banned_cards.return_value = {
            "standard": [],
            "expanded": []
        }
        mock_sets.return_value = {}

        b = Bot("faketoken", False, "123")

        mock_logger_instance.reset_mock()
        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == 2

        mock_ctx = MockCtx()
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == "Legal cards list has been updated!"

        mock_sets.side_effect = Exception("sets fail")
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == (
            "Pokemon sets update failed! sets fail"
        )

        mock_logger_instance.reset_mock()
        b.legal_cards = {}
        b.legal_expanded_cards = {}
        mock_legal_cards.side_effect = Exception("legal fail")
        b.get_legal_cards_task()
        mock_logger_instance.info.assert_called_once()
        mock_logger_instance.error.assert_called_once()

        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == (
            "Legal cards update failed! legal fail"
        )

        await b.get_banned_cards(mock_ctx)
        assert mock_ctx.last_response == (
            "Banned cards list has been updated!"
        )

        mock_logger_instance.reset_mock()
        mock_legal_cards.side_effect = None
        mock_banned_cards.side_effect = Exception("ban fail")
        b.get_legal_cards_task()
        mock_logger_instance.info.assert_called_once()
        mock_logger_instance.error.assert_called_once()

        await b.get_banned_cards(mock_ctx)
        assert mock_ctx.last_response == (
            "Banned cards update failed! ban fail"
        )

        mock_logger_instance.reset_mock()
        b.get_banned_cards_task()
        mock_logger_instance.info.assert_called_once()
        mock_logger_instance.error.assert_called_once()

        mock_logger_instance.reset_mock()
        mock_banned_cards.side_effect = None
        b.get_banned_cards_task()
        assert mock_logger_instance.info.call_count == 2

    @patch("src.bot_legalcards.get_legal_cards")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_legal_cards_maintenance(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_legal_cards
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", True, "123")

        assert mock_legal_cards.call_count == 0

        mock_logger_instance.reset_mock()
        b.get_legal_cards_task()
        assert mock_logger_instance.info.call_count == 2
        assert mock_legal_cards.call_count == 0

        mock_ctx = MockCtx()
        await b.get_legal_cards(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        mock_logger_instance.reset_mock()
        b.get_banned_cards_task()
        assert mock_logger_instance.info.call_count == 2
        mock_logger_instance.info.assert_called_with(
            "Won't update banned cards, Maintenance mode is active"
        )

        await b.get_banned_cards(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

    @patch("src.bot.create_logger")
    @patch("src.bot_legalcards.load_card_database")
    @patch("src.bot.discord")
    @patch("src.bot_legalcards.json")
    @patch("builtins.open")
    async def test_load_save(
        self,
        mock_open,
        mock_json,
        mock_discord,
        mock_card_db,
        mock_logger
    ):
        mock_logger_instance = mock_logger.return_value
        mock_json.dump.side_effect = Exception("test")
        mock_card_db.return_value = ({}, {}, {}, 0)
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", True, "123")

        b.load_legal_cards()
        assert b.legal_cards is not None
        assert b.legal_expanded_cards is not None
        assert b.raw_standard_cards != {}
        assert b.raw_expanded_cards != {}

        b.save_banned_cards()
        mock_logger_instance.error.assert_called_once()
