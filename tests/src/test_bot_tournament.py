import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
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
        self.last_respond_kwargs = kwargs

    async def defer(self, ephemeral=False):
        return

    async def send(self, message, *args, **kwargs):
        self.last_send = message
        self.last_send_kwargs = kwargs


def create_tournament(expiry_days=2, format="standard"):
    """Helper to create a tournament dict that is open"""
    return {
        "name": "Test Tournament",
        "format": format,
        "expires_at": (
            datetime.now() + timedelta(days=expiry_days)
        ).isoformat(sep=" ", timespec="seconds"),
        "created_at": datetime.now().isoformat(sep=" ", timespec="seconds")
    }


def create_closed_tournament(expiry_days=-1, format="standard"):
    """Helper to create a tournament dict that is closed"""
    return {
        "name": "Closed Tournament",
        "format": format,
        "expires_at": (
            datetime.now() + timedelta(days=expiry_days)
        ).isoformat(sep=" ", timespec="seconds"),
        "created_at": datetime.now().isoformat(sep=" ", timespec="seconds")
    }


class TestBotTournament(unittest.IsolatedAsyncioTestCase):

    async def test_tournament_selection_and_views(self):
        b = Bot("faketoken", False, "123")
        ctx = MockCtx()
        tournament = {"one": create_tournament()}

        assert await b.get_tournament_selection(ctx, {}) is None
        assert await b.get_tournament_selection(ctx, tournament) == "one"

        b.user_decklists = {}
        signup_view = __import__(
            "src.bot_tournament", fromlist=["TournamentSignupView"]
        ).TournamentSignupView(b, tournament, str(ctx.author.id))
        interaction = MagicMock()
        interaction.response.send_modal = AsyncMock()
        await signup_view.show_deck_choice(interaction, "one")
        interaction.response.send_modal.assert_awaited_once()

        b.user_decklists = {
            str(ctx.author.id): {
                "saved": {"url": "https://example.com/deck"}
            }
        }
        signup_view = __import__(
            "src.bot_tournament", fromlist=["TournamentSignupView"]
        ).TournamentSignupView(b, tournament, str(ctx.author.id))
        interaction.response.edit_message = AsyncMock()
        await signup_view.show_deck_choice(interaction, "one")
        interaction.response.edit_message.assert_awaited_once()

        saved_view = __import__(
            "src.bot_tournament", fromlist=["SavedDeckSelectView"]
        ).SavedDeckSelectView(b, "one", b.user_decklists[str(ctx.author.id)])
        select = saved_view.children[0]
        interaction.response.send_modal = AsyncMock()
        with patch.object(
            type(select), "values", new_callable=PropertyMock,
            return_value=["saved"],
        ):
            await select.callback(interaction)
        interaction.response.send_modal.assert_awaited_once()

    async def test_tournament_selection_and_signup_error_branches(self):
        b = Bot("faketoken", False, "123")
        ctx = MockCtx()
        open_tournaments = {
            "one": create_tournament(),
            "two": create_tournament(),
        }

        with patch("src.bot_tournament.TournamentSelectView") as view_class:
            view = view_class.return_value
            view.wait = AsyncMock(side_effect=Exception("timeout"))
            assert await b.get_tournament_selection(ctx, open_tournaments) is None

        with patch("src.bot_tournament.TournamentSelectView") as view_class:
            view = view_class.return_value
            view.wait = AsyncMock()
            view.selected_tournament_id = "two"
            assert await b.get_tournament_selection(ctx, open_tournaments) == "two"

        b.tournaments = {"invalid": {"expires_at": "bad"}}
        assert b.get_open_tournaments() == {}
        with patch("builtins.open", side_effect=OSError("write failed")):
            b.save_tournaments()

        b.get_open_tournaments = MagicMock(return_value=open_tournaments)
        b.get_tournament_selection = AsyncMock(return_value=None)
        await b.tournament_signup(ctx, "Name", 1, 2000, "deck")
        assert ctx.last_response == "No tournament selected."
        await b.tournament_signup_url(
            ctx, "Name", 1, 2000, "https://example.com/deck"
        )
        assert ctx.last_response == "No tournament selected."

        b.get_tournament_selection = AsyncMock(return_value="missing")
        await b.tournament_signup(ctx, "Name", 1, 2000, "deck")
        assert ctx.last_response == "Selected tournament is not open."
        await b.tournament_signup_url(
            ctx, "Name", 1, 2000, "https://example.com/deck"
        )
        assert ctx.last_response == "Selected tournament is not open."

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
        # Create an open tournament instead of using tournament_signup_expires_at
        b.tournaments["test_tournament"] = create_tournament()

        assert b.tournament_channels == {}
        assert b.tournament_signups == {}

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

        await b.export_tournament_signups(mock_ctx)
        assert mock_ctx.last_response == "No tournament sign-ups to list."

        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "test_tournament"
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
            "test_tournament"
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
            "test_tournament"
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
            "test_tournament"
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
            "test_tournament"
        )
        mock_fill.assert_called_once()
        assert mock_ctx.last_send == (
            "New tournament signup:\n"
            "- Format: standard\n"
            "- Name: test person (testuser)\n"
            "- Pokémon ID: 1234\n- Year of Birth: 1990\n"
            "- Decklist: https://my.limitlesstcg.com/builder?i=abc123abc\n"
            "- Tournament: Test Tournament"
        )
        assert mock_ctx.last_response == (
            "Tournament signup has been processed!"
        )
        assert mock_ctx.last_respond_kwargs["ephemeral"] is True
        assert mock_ctx.last_respond_kwargs["file"].filename == (
            "sign_up_sheet.png"
        )
        assert mock_ctx.last_send_kwargs["file"].filename == (
            "sign_up_sheet.png"
        )
        mock_remove.assert_called_once()

        await b.export_tournament_signups(mock_ctx)
        assert mock_ctx.last_response.startswith("```csv\n")
        assert "pokemon_id" in mock_ctx.last_response
        assert "test person" in mock_ctx.last_response
        assert "file" not in mock_ctx.last_respond_kwargs

        await b.tournament_signup_url(
            mock_ctx,
            "updated person",
            1234,
            1991,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "test_tournament"
        )
        signups = b.tournament_signups[str(mock_ctx.guild.id)]
        assert len(signups) == 1
        assert signups[0]["full_name"] == "updated person"
        assert signups[0]["year_of_birth"] == 1991

        mock_validate.return_value = (False, "err")
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc",
            "test_tournament"
        )
        assert mock_ctx.last_response == "Deck is not valid: err"

    async def test_tournament_signup_persistence_and_listing_by_tournament(self):
        b = Bot("faketoken", False, "123")
        mock_ctx = MockCtx()
        guild_key = str(mock_ctx.guild.id)
        b.tournament_signups = {}

        b.tournaments["open_tournament"] = create_tournament(2)
        b.tournaments["open_tournament"]["name"] = "Open Tourney"
        b.tournaments["closed_tournament"] = create_closed_tournament(-1)
        b.tournaments["closed_tournament"]["name"] = "Closed Tourney"

        b.record_tournament_signup(
            mock_ctx.guild.id,
            mock_ctx.author.id,
            "Alice",
            111,
            1990,
            "https://example.com/deck1",
            "standard",
            "open_tournament",
        )
        b.record_tournament_signup(
            mock_ctx.guild.id,
            mock_ctx.author.id,
            "Bob",
            222,
            1991,
            "https://example.com/deck2",
            "expanded",
            "closed_tournament",
        )
        b.save_tournament_signups()

        b.tournament_signups = {}
        b.load_tournament_signups()
        assert len(b.tournament_signups[guild_key]) == 2

        await b.export_tournament_signups(mock_ctx)
        response = mock_ctx.last_response

        assert "Open Tourney" in response
        assert "Closed Tourney" in response
        assert "Alice" in response
        assert "Bob" in response
        assert "open_tournament" not in response.lower()

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
        b.tournament_signup_expires_at = (
            datetime.now().replace(microsecond=0).isoformat(sep=" ")
        )
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
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        b.maintenance = False
        # Don't create any tournaments - they should all be closed
        await b.tournament_signup_url(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "No tournaments are open at this moment."
        )

        b.maintenance = True
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
        # Create an open tournament
        b.tournaments["test_tournament"] = create_tournament()

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
            mock_ctx, "first last", 12, 2000, "baddeck"
        )
        assert mock_ctx.last_response == "Deck not found"

        b.maintenance = True
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        b.maintenance = False
        # No tournaments - should show error
        b.tournaments = {}
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == (
            "No tournaments are open at this moment."
        )

        # Create a closed tournament (should fail)
        b.tournaments["closed_tournament"] = create_closed_tournament()
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == (
            "No tournaments are open at this moment."
        )

        # Create an open tournament
        b.tournaments["test_tournament"] = create_tournament()
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == (
            "Legal cards are not loaded. Please try again later."
        )

        b.legal_cards = {"something": "here"}
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == OUTPUT_CHANNEL_NOT_SET_ERROR

        b.tournament_channels = {"202": "123"}
        mock_sign_up_sheet = MagicMock()
        mock_sign_up_sheet.return_value = False
        b.check_sign_up_sheet = mock_sign_up_sheet
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        assert mock_ctx.last_response == SIGN_UP_SHEET_MISSING_ERROR

        mock_sign_up_sheet.return_value = True
        b.tournament_signup_response = AsyncMock()
        mock_validate.return_value = (False, "the error")
        await b.tournament_signup(
            mock_ctx, "first last", 12, 2000, "deckname"
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
            mock_ctx, "first last", 12, 2000, "deckname"
        )
        deck_info = b.user_decklists["303"]["deckname"]
        for format in ("standard", "expanded"):
            assert deck_info[format]["valid"]
            assert deck_info[format]["error"] == ""
        b.tournament_signup_response.assert_called_once()

    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_tournament_signup_status_messages(
        self,
        mock_open,
        mock_discord,
        mock_logger,
    ):
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", False, "123")

        is_open, message = b.get_tournament_signup_status()
        assert is_open is False
        assert message == "no tournaments are being held at this moment"

        b.tournament_signup_expires_at = (
            (datetime.now() - timedelta(hours=2)).isoformat(sep=" ")
        )
        is_open, message = b.get_tournament_signup_status()
        assert is_open is False
        assert message == "tournament sign ups are closed"

        b.tournament_signup_expires_at = (
            (datetime.now() - timedelta(days=2)).isoformat(sep=" ")
        )
        is_open, message = b.get_tournament_signup_status()
        assert is_open is False
        assert message == "no tournaments are being held at this moment"

        b.tournament_signup_expires_at = (
            (datetime.now() + timedelta(hours=2)).isoformat(sep=" ")
        )
        is_open, message = b.get_tournament_signup_status()
        assert is_open is True
        assert message is None

        b.tournament_signup_expires_at = "invalid-datetime"
        is_open, message = b.get_tournament_signup_status()
        assert is_open is False
        assert message == "no tournaments are being held at this moment"
