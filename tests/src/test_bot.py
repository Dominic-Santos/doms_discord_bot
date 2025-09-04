from unittest.mock import patch, MagicMock
from src.bot import Bot


@patch("src.bot.create_logger")
@patch("src.bot.discord")
@patch("builtins.open")
def test_bot_init(
    mock_open,
    mock_discord,
    mock_logger,
):
    mock_bot = MagicMock()
    mock_discord.Bot.return_value = mock_bot

    b = Bot("faketoken", False, "123")

    mock_discord.Bot.assert_called_once()
    assert mock_open.call_count == 10
    mock_logger.assert_called_once()

    b.add_tasks()
    b.run()

    mock_bot.run.assert_called_once()
