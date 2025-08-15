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
        self.author = MagicMock()
        self.author.id = 303
        self.author.mention = "testuser"

    async def respond(self, message, *args, **kwargs):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return

    async def send(self, message, *args, **kwargs):
        self.last_send = message


class TestBotDecklist(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_decklist.os.remove")
    @patch("src.bot_decklist.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_decklist.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_newsfeed.json")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_signup_sheet(
        self,
        mock_load,
        mock_open,
        mock_dl_json,
        mock_nf_json,
        mock_discord,
        mock_logger,
        mock_sign_sheet,
        mock_decklist,
        mock_validate,
        mock_fill,
        mock_remove
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

        mock_dl_json.load = raise_exception

        b = Bot("faketoken", False, "123")

        assert mock_logger_instance.info.call_count == 2
        assert b.output_channels == {}

        mock_dl_json.dump = raise_exception
        b.save_output_channels()
        mock_logger_instance.error.assert_called_once()

        mock_ctx = MockCtx()
        await b.test_output_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Output channel is not set for this server."
        )

        await b.set_output_channel(mock_ctx)
        assert mock_ctx.last_response == "Output channel set to test channel!"

        mock_bot.get_channel.return_value = None
        await b.test_output_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Output channel not found. Please set it again."
        )

        mock_bot.get_channel.return_value = mock_ctx
        await b.test_output_channel(mock_ctx)
        assert mock_ctx.last_response == (
            "Test message sent to the output channel!"
        )
        assert mock_ctx.last_send == "This is a test message from the bot!"

        assert b.check_sign_up_sheet() in [True, False]

        assert b.check_limitless_url(
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert b.check_limitless_url(
            "y.limitlesstcg.com/builder?i=abc123abc"
        ) is False

        b.update_signup_sheet_task()

        assert mock_logger_instance.info.call_count == 4

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == "Sheet has been updated!"

        mock_decklist.return_value = {}
        mock_validate.return_value = (True, "")
        await b.decklist_check(mock_ctx, "https://my.com/builder?i=abc123abc")
        assert mock_ctx.last_response == (
            "Decklist is not valid: Invalid Limitless URL."
        )

        await b.decklist_check(
            mock_ctx,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == "Decklist is valid!"

        await b.tournament_signup(
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
        await b.tournament_signup(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Output channel not found. Please set it again."
        )

        mock_bot.get_channel.return_value = mock_ctx
        mock_sign_up_sheet = MagicMock()
        mock_sign_up_sheet.return_value = False
        b.check_sign_up_sheet = mock_sign_up_sheet
        await b.tournament_signup(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Sign-up sheet is not available. Please try again later."
        )

        mock_sign_up_sheet.return_value = True
        await b.tournament_signup(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Decklist is not valid: Invalid Limitless URL."
        )
        await b.tournament_signup(
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
    @patch("src.bot_decklist.fill_sheet")
    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot_decklist.get_sign_up_sheet")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_newsfeed.json")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_singup_sheet_errors(
        self,
        mock_load,
        mock_open,
        mock_dl_json,
        mock_nf_json,
        mock_discord,
        mock_logger,
        mock_sign_sheet,
        mock_decklist,
        mock_validate,
        mock_fill,
        mock_remove
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

        mock_dl_json.load = raise_exception
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
    @patch("src.bot_newsfeed.json")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    @patch("src.bot_legalcards.load_card_database")
    async def test_bot_signup_sheet_maintenance(
        self,
        mock_load,
        mock_open,
        mock_dl_json,
        mock_nf_json,
        mock_discord,
        mock_logger,
    ):
        mock_load.return_value = ({}, {})
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_logger_instance = mock_logger.return_value

        b = Bot("faketoken", True, "123")

        mock_ctx = MockCtx()

        await b.decklist_check(mock_ctx, "https://my.com/builder?i=abc123abc")
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.tournament_signup(
            mock_ctx,
            "test person",
            1234,
            1990,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        await b.update_signup_sheet(mock_ctx)
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

        assert mock_logger_instance.info.call_count == 1
        b.update_signup_sheet_task()
        assert mock_logger_instance.info.call_count == 3
