import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.bot import Bot


class MockCtx():
    def __init__(self):
        self.guild = MagicMock()
        self.guild.id = 202

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
        assert b.tournament_signups[str(mock_ctx.guild.id)] == []

        b.tournament_signups[str(mock_ctx.guild.id)] = [{"full_name": "x"}]
        await b.open_tournament_signups(
            mock_ctx,
            future_dt,
            b.password
        )
        assert b.tournament_signups[str(mock_ctx.guild.id)] == []

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
            "No tournaments created yet."
        )

        # Create a tournament and check status
        b.tournaments["test"] = {
            "name": "Test Tournament",
            "format": "standard",
            "expires_at": "2026-05-21 18:30:00",
            "created_at": "2026-05-20 00:00:00"
        }
        await b.tournament_status(mock_ctx)
        assert "Test Tournament" in mock_ctx.last_response
        assert "2026-05-21 18:30:00" in mock_ctx.last_response

        await b.close_tournament_signups(mock_ctx, "fake")
        assert mock_ctx.last_response == "Invalid admin password"

        await b.close_tournament_signups(mock_ctx, b.password)
        assert mock_ctx.last_response == "Tournament sign-ups are now closed."
        assert b.tournament_signup_expires_at is None

        b.tournaments = {
            "open_one": {
                "name": "Open One",
                "format": "standard",
                "expires_at": "2099-05-21 18:30:00",
            },
            "open_two": {
                "name": "Open Two",
                "format": "expanded",
                "expires_at": "2099-06-21 18:30:00",
            },
        }
        await b.close_tournament(mock_ctx, "open_one", "fake")
        assert mock_ctx.last_response == "Invalid admin password"
        assert b.tournaments["open_one"]["expires_at"] == (
            "2099-05-21 18:30:00"
        )

        await b.close_tournament(mock_ctx, "missing", b.password)
        assert mock_ctx.last_response == "Tournament 'missing' not found."

        await b.close_tournament(mock_ctx, "open_one", b.password)
        assert mock_ctx.last_response == (
            "Tournament 'Open One' is now closed."
        )
        assert datetime.fromisoformat(
            b.tournaments["open_one"]["expires_at"]
        ) <= datetime.now()
        assert b.tournaments["open_two"]["expires_at"] == (
            "2099-06-21 18:30:00"
        )

        b.tournaments["closed"] = {
            "name": "Closed",
            "expires_at": "2000-01-01 00:00:00",
        }
        b.tournaments["invalid"] = {
            "name": "Invalid",
            "expires_at": "not a datetime",
        }
        await b.delete_closed_tournaments(mock_ctx, "fake")
        assert mock_ctx.last_response == "Invalid admin password"
        assert "closed" in b.tournaments

        await b.delete_closed_tournaments(mock_ctx, b.password)
        assert mock_ctx.last_response == "Deleted 1 closed tournament(s)."
        assert "closed" not in b.tournaments
        assert "open_two" in b.tournaments
        assert "invalid" in b.tournaments
