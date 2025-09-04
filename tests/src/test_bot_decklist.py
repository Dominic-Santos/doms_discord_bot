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


class TestBotDecklist(unittest.IsolatedAsyncioTestCase):

    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
    @patch("src.bot.create_logger")
    @patch("src.bot.discord")
    @patch("src.bot_decklist.json")
    @patch("builtins.open")
    async def test_bot_decklist(
        self,
        mock_open,
        mock_dl_json,
        mock_discord,
        mock_logger,
        mock_decklist,
        mock_validate,
    ):
        mock_logger_instance = mock_logger.return_value
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot

        mock_dl_json.load.side_effect = Exception("failed")

        b = Bot("faketoken", False, "123")

        assert b.tournament_channels == {}

        mock_dl_json.dump.side_effect = Exception("failed")
        b.save_user_decklists()
        mock_logger_instance.error.assert_called_once()

        mock_ctx = MockCtx()

        assert b.check_limitless_url(
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert b.check_limitless_url(
            "y.limitlesstcg.com/builder?i=abc123abc"
        ) is False

        mock_decklist.return_value = {}
        mock_validate.return_value = (True, "")
        await b.decklist_check_url(
            mock_ctx, "https://my.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Error checking deck: Invalid Limitless URL."
        )

        await b.decklist_check_url(
            mock_ctx,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck check complete:\n- standard valid!\n- expanded valid!"
        )

        mock_validate.return_value = (False, "err")
        await b.decklist_check_url(
            mock_ctx,
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck check complete:\n"
            "- standard not valid! err\n"
            "- expanded not valid! err"
        )

        mock_decklist.side_effect = Exception("failed")
        valid, deck, error = b.do_decklist_check(
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert valid == {}
        assert deck == {}
        assert error == "failed"

        b.maintenance = True
        await b.decklist_check_url(
            mock_ctx, "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == MAINTENANCE_MODE_MESSAGE

    @patch("src.bot_decklist.validate_decklist")
    @patch("src.bot_decklist.get_decklist_from_url")
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
        mock_decklist,
        mock_validate,
    ):
        mock_bot = MagicMock()
        mock_discord.Bot.return_value = mock_bot
        mock_dl_json.load.side_effect = Exception("failed")
        mock_dl_json.dump.side_effect = Exception("failed")

        mock_ctx = MockCtx()
        b = Bot("faketoken", False, "123")
        assert b.user_decklists == {}

        valid, error = b.do_user_decklist_check("123", "noname")
        assert valid is None
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
        assert valid is not None
        assert error is None
        for format in ("standard", "expanded"):
            assert b.user_decklists["123"]["deckname"][format]["valid"]
            assert b.user_decklists["123"]["deckname"][format]["error"] == ""
        assert b.user_decklists["123"]["deckname"]["last_checked"] != ""
        assert b.user_decklists["123"]["deckname"]["deck"] == {}

        b.user_decklists = {
            "123": {
                "deckname": {
                    "url": "https://my.lsstcg.com/builder?i=abc123abc"
                }
            }
        }
        valid, error = b.do_user_decklist_check("123", "deckname")
        assert valid == {}
        assert error == "Invalid Limitless URL."
        for format in ("standard", "expanded"):
            deck_data = b.user_decklists["123"]["deckname"][format]
            assert deck_data["valid"] is False
            assert deck_data["error"] == "Invalid Limitless URL."

        b.user_decklists = {}
        b.do_user_decklist_check = MagicMock()
        b.do_user_decklist_check.return_value = ({
            "standard": {
                "valid": True,
                "error": ""
            },
            "expanded": {
                "valid": True,
                "error": ""
            }
        }, None)
        await b.decklist_create(
            mock_ctx,
            "deckname",
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck saved, deck is:\n"
            "- standard valid!\n"
            "- expanded valid!"
        )
        assert "303" in b.user_decklists
        assert "deckname" in b.user_decklists["303"]
        assert b.user_decklists["303"]["deckname"]["url"] == (
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )

        b.do_user_decklist_check.return_value = ({
            "standard": {
                "valid": False,
                "error": "err"
            },
            "expanded": {
                "valid": False,
                "error": "err2"
            }
        }, None)
        await b.decklist_create(
            mock_ctx,
            "deckname",
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck saved, deck is:\n"
            "- standard not valid! err\n"
            "- expanded not valid! err2"
        )

        b.do_user_decklist_check.return_value = (False, "err")
        await b.decklist_create(
            mock_ctx,
            "deckname2",
            "https://my.limitlesstcg.com/builder?i=abc123abc"
        )
        assert mock_ctx.last_response == (
            "Deck saved, error checking deck: err"
        )

        await b.decklist_check(mock_ctx, "deckname2")
        assert mock_ctx.last_response == (
            "Error checking deck: err"
        )

        b.do_user_decklist_check.return_value = ({
            "standard": {
                "valid": True,
                "error": ""
            },
            "expanded": {
                "valid": True,
                "error": ""
            }
        }, None)
        await b.decklist_check(mock_ctx, "deckname2")
        assert mock_ctx.last_response == (
            "Deck is:\n- standard valid!\n- expanded valid!"
        )

        b.do_user_decklist_check.return_value = ({
            "standard": {
                "valid": False,
                "error": "err"
            },
            "expanded": {
                "valid": False,
                "error": "err2"
            }
        }, None)
        await b.decklist_check(mock_ctx, "deckname2")
        assert mock_ctx.last_response == (
            "Deck is:\n"
            "- standard not valid! err\n"
            "- expanded not valid! err2"
        )

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
                    "standard": {
                        "valid": False,
                        "error": "not 60 cards"
                    },
                    "expanded": {
                        "valid": False,
                        "error": "not 60 cards"
                    },
                    "last_checked": "2025-12-25",
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
            "deckname\n"
            "Standard Legal: :x: - not 60 cards\n"
            "Expanded Legal: :x: - not 60 cards\n"
            "Last Checked: 2025-12-25\n"
            "Pokemon:\n\t4x Pikachu JTG-25\nTrainers:\n\t3x switch\n"
            "Energies:\n\t2x lightning"
        )
        assert mock_ctx.last_response == expected_deck

        b.user_decklists["303"]["deckname"]["standard"]["valid"] = True
        b.user_decklists["303"]["deckname"]["expanded"]["valid"] = True
        expected_deck = expected_deck.replace(
            ":x:", ":white_check_mark:"
        )
        expected_deck = expected_deck.replace(
            " - not 60 cards", ""
        )
        await b.decklist_info(mock_ctx, "deckname")
        assert mock_ctx.last_response == expected_deck
