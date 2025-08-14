import json
from src.bot import Bot

DEFAULT_MAINTENANCE_MODE = True
DEFAULT_ADMIN_PASSWRD = "abc123"


def main():
    # load config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(
            "config.json not found. Please create it with the required fields."
        )
        return

    # create bot instance
    bot = Bot(
        config.get("app_token"),
        config.get("maintenance_mode", DEFAULT_MAINTENANCE_MODE),
        config.get("admin_password", DEFAULT_ADMIN_PASSWRD)
    )

    # run the bot
    bot.run()


if __name__ == "__main__":
    main()  # pragma: no cover
