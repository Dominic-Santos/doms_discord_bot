import unittest
from unittest.mock import patch, MagicMock
from src.bot import Bot


class MockCtx():
    async def respond(self, message, ephemeral=False):
        self.last_response = message

    async def defer(self, ephemeral=False):
        return


class TestBotAdmin(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("builtins.open")
    async def test_bot_admin(
        self,
        mock_open,
        mock_discord,
        mock_logger,
    ):
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        b = Bot("faketoken", False, "123")

        mock_ctx = MockCtx()
        await b.maintenance_status(mock_ctx)
        assert mock_ctx.last_response == "Maintenance mode: off"
        assert b.maintenance is False

        await b.toggle_maintenance(mock_ctx, "fake")
        assert mock_ctx.last_response == "Invalid admin password"
        assert b.maintenance is False

        await b.toggle_maintenance(mock_ctx, b.password)
        assert mock_ctx.last_response == "Maintenance mode: on"
        assert b.maintenance

        await b.maintenance_status(mock_ctx)
        assert mock_ctx.last_response == "Maintenance mode: on"
        assert b.maintenance

        await b.toggle_maintenance(mock_ctx, b.password)
        assert mock_ctx.last_response == "Maintenance mode: off"
        assert b.maintenance is False
