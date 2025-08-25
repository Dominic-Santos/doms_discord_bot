import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from src.bot import Bot
from src.helpers import MAINTENANCE_MODE_MESSAGE
from src.bot_decklist import (
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


def raise_exception():
    raise Exception("test error")


class TestBotDecklist(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_decklist.os.remove")
    @patch("src.bot_decklist.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_decklist.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    async def test_bot_signup_sheet(
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

        try:
            raise_exception()
        except Exception as e:
            assert str(e) == "test error"

        mock_dl_json.load = raise_exception

        b = Bot("faketoken", False, "123")

        assert b.tournament_channels == {}

        mock_dl_json.dump = raise_exception
        b.save_tournament_channels()
        mock_logger_instance.error.assert_called_once()
        b.save_user_decklists()
        assert mock_logger_instance.error.call_count == 2

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

        assert b.check_limitless_url(
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert b.check_limitless_url(
            "y.limitlesstcg.com/builder?i=abc123abc"
        ) is False

        inf_calls = mock_logger_instance.info.call_count
        b.update_signup_sheet_task()
        assert mock_logger_instance.info.call_count == inf_calls + 2

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == "Sheet has been updated!"

        mock_decklist.return_value = {}
        mock_validate.return_value = (True, "")
        await b.decklist_check_url(
            mock_ctx, "https://my.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Decklist is not valid: Invalid Limitless URL."
        )

        await b.decklist_check_url(
            mock_ctx,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == "Decklist is valid!"

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
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
            "https://my.limitlesstcg.com/builder?i=abc123abc"
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
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == SIGN_UP_SHEET_MISSING_ERROR

        mock_sign_up_sheet.return_value = True
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Decklist is not valid: Invalid Limitless URL."
        )
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        mock_fill.assert_called_once()
        assert mock_ctx.last_send == (
            "New tournament signup:\n- Name: test person (testuser)\n-"
            " Pokémon ID: 1234\n- Year of Birth: 1990\n-"
            " Decklist: https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Tournament signup has been processed!"
        )
        mock_remove.assert_called_once()

    @patch("src.bot_decklist.os.remove")
    @patch("src.bot_decklist.get_sign_up_sheet")
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

        mock_sign_sheet.raiseError.side_effect = raise_exception

        def mock_do_update_sheet():
            return Exception("Test")

        b = Bot("faketoken", False, "123")
        b.do_update_sheet = mock_do_update_sheet

        mock_ctx = MockCtx()
        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response.startswith("Failed")

        b.update_signup_sheet_task()
        assert mock_logger_instance.error.call_count == 1

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

        await b.decklist_check_url(
            mock_ctx, "https://my.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        inf_calls = mock_logger_instance.info.call_count
        b.update_signup_sheet_task()
        assert mock_logger_instance.info.call_count == inf_calls + 2

    @patch("src.bot_decklist.os.remove")
    @patch("src.bot_decklist.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_decklist.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_decklist.json")
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
        mock_dl_json.load = raise_exception
        mock_dl_json.dump = raise_exception

        mock_ctx = MockCtx()
        b = Bot("faketoken", False, "123")
        assert b.user_decklists == {}

        valid, error = b.do_user_decklist_check("123", "noname")
        assert valid is False
        assert error == "Deck not found"

        b.user_decklists = {
            "123": {
                "deckname": {
                    "url": "https://my.limitlesstcg.com/builder?i=abc123abc"
                }
            }
        }
        mock_decklist.return_value = {}
        mock_validate.return_value = (True, "")

        valid, error = b.do_user_decklist_check("123", "deckname")
        assert valid
        assert error == ""
        assert b.user_decklists["123"]["deckname"]["valid"]
        assert b.user_decklists["123"]["deckname"]["last_checked"] != ""
        assert b.user_decklists["123"]["deckname"]["deck"] == {}
        assert b.user_decklists["123"]["deckname"]["error"] == ""

        b.user_decklists = {}
        b.do_user_decklist_check = MagicMock()
        b.do_user_decklist_check.return_value = (True, "")
        await b.decklist_create(
            mock_ctx,
            "deckname",
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == "Deck saved, decklist is valid!"
        assert "303" in b.user_decklists
        assert "deckname" in b.user_decklists["303"]
        assert b.user_decklists["303"]["deckname"]["url"] == (
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )

        b.do_user_decklist_check.return_value = (False, "err")
        await b.decklist_create(
            mock_ctx,
            "deckname2",
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck saved, decklist is not valid! err"
        )

        await b.decklist_check(mock_ctx, "deckname2")
        assert mock_ctx.last_response == (
            "Decklist is not valid! err"
        )

        b.do_user_decklist_check.return_value = (True, "")
        await b.decklist_check(mock_ctx, "deckname2")
        assert mock_ctx.last_response == "Decklist is valid!"

        await b.decklist_delete(mock_ctx, "fakename")
        assert mock_ctx.last_response == "Deck not found"

        await b.decklist_delete(mock_ctx, "deckname2")
        assert mock_ctx.last_response == "Deck was deleted"
        assert len(b.user_decklists["303"]) == 1

        await b.decklist_list(mock_ctx)
        assert mock_ctx.last_response == "Your decks:\n\tdeckname"

        b.user_decklists = {}
        await b.decklist_list(mock_ctx)
        assert mock_ctx.last_response == "You have no saved decks"

        await b.decklist_info(mock_ctx, "deckname")
        assert mock_ctx.last_response == "Deck not found"

        b.user_decklists = {
            "303": {
                "deckname": {
                    "url": "https://my.limitlesstcg.com/builder?i=abc123abc",
                    "valid": False,
                    "last_checked": "2025-12-25",
                    "error": "not 60 cards",
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
        await b.decklist_info(mock_ctx, "deckname")
        expected_deck = (
            "deckname\nStandard Legal: :x: (2025-12-25)\nError: not 60 cards\n"
            "Pokemon:\n\t4x Pikachu JTG-25\nTrainers:\n\t3x switch\n"
            "Energies:\n\t2x lightning"
        )
        assert mock_ctx.last_response == expected_deck

        b.user_decklists["303"]["deckname"]["valid"] = True
        expected_deck = expected_deck.replace(
            ":x:", ":white_check_mark:"
        )
        expected_deck = expected_deck.replace(
            "\nError: not 60 cards", ""
        )
        await b.decklist_info(mock_ctx, "deckname")
        assert mock_ctx.last_response == expected_deck

        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "baddeck")
        assert mock_ctx.last_response == "Deck not found"

        b.maintenance = True
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        b.maintenance = False
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert mock_ctx.last_response == (
            "Legal cards are not loaded. Please try again later."
        )

        b.legal_cards = {"something": "here"}
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_SET_ERROR

        b.tournament_channels = {"202": "123"}
        mock_sign_up_sheet = MagicMock()
        mock_sign_up_sheet.return_value = False
        b.check_sign_up_sheet = mock_sign_up_sheet
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert mock_ctx.last_response == SIGN_UP_SHEET_MISSING_ERROR

        mock_sign_up_sheet.return_value = True
        b.tournament_signup_response = AsyncMock()
        mock_validate.return_value = (False, "the error")
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert b.user_decklists["303"]["deckname"]["valid"] is False
        assert b.user_decklists["303"]["deckname"]["error"] == "the error"
        assert b.user_decklists["303"]["deckname"]["last_checked"] == (
            str(datetime.now().date())
        )
        assert b.tournament_signup_response.call_count == 0

        mock_validate.return_value = (True, "")
        await b.tournament_signup(mock_ctx, "first last", 12, 2000, "deckname")
        assert b.user_decklists["303"]["deckname"]["valid"]
        assert b.user_decklists["303"]["deckname"]["error"] == ""
        assert b.tournament_signup_response.call_count == 1
