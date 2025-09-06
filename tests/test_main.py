from main import main
from unittest.mock import patch, mock_open


@patch("main.Bot")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"app_token": "test_token"}'
)
def test_main(mock_file_open, mock_bot):
    main()

    # Check if the config file was opened
    mock_file_open.assert_called_once_with("config.json", "r")

    # Check if the Bot was instantiated with the correct token
    mock_bot.assert_called_once_with("test_token", True, "abc123")

    # Check if the bot's run method was called
    mock_bot.return_value.run.assert_called_once()


@patch("builtins.open", new_callable=mock_open)
@patch("builtins.print")
def test_main_no_config(mock_print, mock_file_open):
    mock_file_open.side_effect = FileNotFoundError

    main()

    # Check if the error message was printed
    mock_print.assert_called_once_with(
        "config.json not found. Please create it with the required fields."
    )
