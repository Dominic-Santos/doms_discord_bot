import json
from src.bot import Bot

def main():
    
    # load config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("config.json not found. Please create it with the required fields.")
        exit(1)

    # create bot instance
    bot = Bot(config.get("app_token"))

    # run the bot
    bot.run()


if __name__ == "__main__":
    main()
