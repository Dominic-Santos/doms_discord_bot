from unittest.mock import patch, MagicMock
from src.bot import Bot

@patch("src.bot.tasks")
@patch("src.bot.create_logger")
@patch("src.bot.discord")
@patch("src.bot_newsfeed.json")
@patch("src.bot_decklist.json")
@patch("builtins.open")
@patch("src.bot_legalcards.load_card_database")
def test_bot_init(
    mock_load,
    mock_open,
    mock_dl_json,
    mock_nf_json,
    mock_discord,
    mock_logger,
    mock_tasks
):
    mock_load.return_value = ({}, {}, {})
    mock_bot = MagicMock()
    mock_discord.Bot.return_value = mock_bot

    b = Bot("faketoken")

    mock_dl_json.load.assert_called_once()
    mock_nf_json.load.assert_called_once()
    
    mock_discord.Bot.assert_called_once()
    assert mock_open.call_count == 2
    mock_logger.assert_called_once()

    b.add_tasks()
    b.run()

    mock_bot.run.assert_called_once()
