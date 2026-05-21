import unittest
from datetime import datetime, timedelta
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

        await b.open_tournament_signups(
            mock_ctx,
            (datetime.now() + timedelta(hours=2)).isoformat(sep=" "),
            "fake"
        )
        assert mock_ctx.last_response == "Invalid admin password"

        await b.open_tournament_signups(
            mock_ctx,
            "not a datetime",
            b.password
        )
        assert mock_ctx.last_response.startswith("Invalid datetime format")

        future_dt = (datetime.now() + timedelta(hours=3)).isoformat(sep=" ")
        await b.open_tournament_signups(
            mock_ctx,
            future_dt,
            b.password
        )
        assert mock_ctx.last_response.startswith(
            "Tournament sign-ups are now open until"
        )
        assert b.tournament_signup_expires_at is not None

        await b.open_tournament_signups(
            mock_ctx,
            "2026-05-21T18:30:00+00:00",
            b.password
        )
        assert mock_ctx.last_response.startswith(
            "Tournament sign-ups are now open until"
        )

        b.tournament_signup_expires_at = None
        await b.tournament_status(mock_ctx)
        assert mock_ctx.last_response == (
            "No tournament sign-ups are currently open."
        )

        b.tournament_signup_expires_at = "2026-05-21 18:30:00"
        await b.tournament_status(mock_ctx)
        assert mock_ctx.last_response == (
            "Tournament sign-ups expire at 2026-05-21 18:30:00"
        )
