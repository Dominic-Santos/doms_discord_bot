import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from src.bot import Bot
from src.helpers import MAINTENANCE_MODE_MESSAGE
from src.bot_tournament import (
    OUTPUT_CHANNEL_NOT_SET_ERROR,
    OUTPUT_CHANNEL_NOT_FOUND_ERROR,
    TEST_MESSAGE,
    SIGN_UP_SHEET_MISSING_ERROR
)


class MockCtx():
    def __init__(self):
        self.channel = MagicMock()
        self.channel.id = 101
        self.channel.name = "test channel"
        self.guild = MagicMock()
        self.guild.id = 202
        self.author = MagicMock()
        self.author.id = 303
        self.author.mention = "testuser"

    async def respond(self, message, *args, **kwargs):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return

    async def send(self, message, *args, **kwargs):
        self.last_send = message


class TestBotTournament(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_tournament.os.remove")
    @patch("src.bot_tournament.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_tournament.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_tournament.json")
    @patch("builtins.open")
    async def test_bot_tournament(
        self,
        mock_open,
        mock_dl_json,
        mock_discord,
        mock_logger,
        mock_sign_sheet,
        mock_decklist,
        mock_validate,
        mock_fill,
        mock_remove
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        mock_dl_json.load.side_effect = Exception("failed")

        b = Bot("faketoken", False, "123")

        assert b.tournament_channels == {}

        mock_dl_json.dump.side_effect = Exception("failed")
        b.save_tournament_channels()
        mock_logger_instance.error.assert_called_once()

        mock_ctx = MockCtx()
        await b.test_tournament_channel(mock_ctx)
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_SET_ERROR

        await b.set_tournament_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Tournament output channel set to test channel!"
        )

        mock_bot.get_channel.return_value = None
        await b.test_tournament_channel(mock_ctx)
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_FOUND_ERROR

        mock_bot.get_channel.return_value = mock_ctx
        await b.test_tournament_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Test message sent to the output channel!"
        )
        assert mock_ctx.last_send == TEST_MESSAGE

        assert b.check_sign_up_sheet() in [True, False]

        mock_logger_instance.reset_mokc()
        b.update_signup_sheet_task()
        assert mock_logger_instance.info.call_count == 2

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == "Sheet has been updated!"

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == (
            "Legal cards are not loaded. Please try again later."
        )

        b.legal_cards = {"something": "here"}
        mock_bot.get_channel.return_value = None
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_FOUND_ERROR

        mock_bot.get_channel.return_value = mock_ctx
        mock_sign_up_sheet = MagicMock()
        mock_sign_up_sheet.return_value = False
        b.check_sign_up_sheet = mock_sign_up_sheet
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == SIGN_UP_SHEET_MISSING_ERROR

        mock_sign_up_sheet.return_value = True
        mock_validate.return_value = (True, "")
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == (
            "Error checking decklist: Invalid Limitless URL."
        )

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        mock_fill.assert_called_once()
        assert mock_ctx.last_send == (
            "New tournament signup:\n"
            "- Format: standard\n"
            "- Name: test person (testuser)\n"
            "- Pokémon ID: 1234\n- Year of Birth: 1990\n"
            "- Decklist: https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Tournament signup has been processed!"
        )
        mock_remove.assert_called_once()

        mock_validate.return_value = (False, "err")
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == "Deck is not valid: err"

    @patch("src.bot_tournament.os.remove")
    @patch("src.bot_tournament.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_singup_sheet_errors(
        self,
        mock_open,
        mock_discord,
        mock_logger,
        mock_sign_sheet,
        mock_remove
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        mock_sign_sheet.side_effect = Exception("failed")

        def mock_do_update_sheet():
            return Exception("Test")

        b = Bot("faketoken", False, "123")
        b.do_update_sheet = mock_do_update_sheet

        mock_ctx = MockCtx()
        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response.startswith("Failed")

        b.update_signup_sheet_task()
        mock_logger_instance.error.assert_called_once()

    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_signup_sheet_maintenance(
        self,
        mock_open,
        mock_discord,
        mock_logger,
    ):
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_logger_instance = mock_logger.return_value

        b = Bot("faketoken", True, "123")

        mock_ctx = MockCtx()

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "standard"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        mock_logger_instance.reset_mock()
        b.update_signup_sheet_task()
        assert mock_logger_instance.info.call_count == 2

    @patch("src.bot_tournament.os.remove")
    @patch("src.bot_tournament.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_tournament.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_tournament.json")
    @patch("builtins.open")
    async def test_bot_user_decklists(
        self,
        mock_open,
        mock_dl_json,
        mock_discord,
        mock_logger,
        mock_sign_sheet,
        mock_decklist,
        mock_validate,
        mock_fill,
        mock_remove
    ):
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_dl_json.load.side_effect = Exception("failed")
        mock_dl_json.dump.side_effect = Exception("failed")

        mock_ctx = MockCtx()
        b = Bot("faketoken", False, "123")

        mock_decklist.return_value = {}
        mock_validate.return_value = (True, "")
        b.user_decklists = {
            "303": {
                "deckname": {
                    "url": "https://my.limitlesstcg.com/builder?i=abc123abc",
                    "last_checked": "2025-12-25",
                    "standard": {
                        "valid": False,
                        "error": "not 60 cards"
                    },
                    "expanded": {
                        "valid": False,
                        "error": "not 60 cards"
                    },
                    "deck": {
                        "pokemon": [
                            {
                                "name": "Pikachu",
                                "number": "25",
                                "quantity": 4,
                                "set": "JTG"
                            }
                        ],
                        "trainers": {
                            "switch": {
                                "quantity": 3
                            }
                        },
                        "energies": {
                            "lightning": {
                                "quantity": 2
                            }
                        }
                    }
                }
            }
        }

        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "baddeck", "standard"
        )
        assert mock_ctx.last_response == "Deck not found"

        b.maintenance = True
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        b.maintenance = False
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        assert mock_ctx.last_response == (
            "Legal cards are not loaded. Please try again later."
        )

        b.legal_cards = {"something": "here"}
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_SET_ERROR

        b.tournament_channels = {"202": "123"}
        mock_sign_up_sheet = MagicMock()
        mock_sign_up_sheet.return_value = False
        b.check_sign_up_sheet = mock_sign_up_sheet
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        assert mock_ctx.last_response == SIGN_UP_SHEET_MISSING_ERROR

        mock_sign_up_sheet.return_value = True
        b.tournament_signup_response = AsyncMock()
        mock_validate.return_value = (False, "the error")
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        deck_info = b.user_decklists["303"]["deckname"]
        for format in ("standard", "expanded"):
            assert deck_info[format]["valid"] is False
            assert deck_info[format]["error"] == "the error"
        assert deck_info["last_checked"] == (
            str(datetime.now().date())
        )
        assert b.tournament_signup_response.call_count == 0

        mock_validate.return_value = (True, "")
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname", "standard"
        )
        deck_info = b.user_decklists["303"]["deckname"]
        for format in ("standard", "expanded"):
            assert deck_info[format]["valid"]
            assert deck_info[format]["error"] == ""
        b.tournament_signup_response.assert_called_once()
