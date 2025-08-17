import datetime
import discord

from discord.ext import tasks

from .helpers import create_logger
from .bot_decklist import DecklistBot
from .bot_legalcards import LegalCardsBot
from .bot_newsfeed import NewsfeedBot
from .bot_admin import AdminBot
from .bot_events import EventsBot


class Bot(DecklistBot, LegalCardsBot, NewsfeedBot, AdminBot, EventsBot):
    def __init__(self, token: str, maintenance_mode: bool, password: str):
        self.bot = discord.Bot()
        self.token = token
        self.maintenance = maintenance_mode
        self.password = password
        self.logger = create_logger("decklist_bot", filename="logs/bot.log")

        self.load_legal_cards()
        self.load_output_channels()
        self.load_newsfeed_channels()
        self.load_events_data()
        self.add_commands()

    def add_commands(self):
        self.admin = self.bot.create_group("admin", "Admin commands")
        self.add_event_commands()
        self.add_newsfeed_commands()
        self.add_legal_cards_commands()
        self.add_decklist_commands()
        self.add_admin_commands()

        @self.bot.command(description="Get information about the bot")
        async def about(ctx):
            await ctx.respond(
                (
                    "This is a Discord bot built for managing Pokémon "
                    "TCG events and News.\n\n"
                    "It can validate decklists, manage tournament sign-ups,"
                    " and provide news updates from PokéBeach.\n\n"
                    "Created by Dominic Santos "
                    "(dominatordom8125 on Discord)"
                ),
                ephemeral=True
            )  # pragma: no cover

        @self.bot.command(description="Help Documentation")
        async def help(ctx):
            await ctx.respond(
                (
                    "Readme available at "
                    "https://github.com/Dominic-Santos/doms_discord_bot"
                ),
                ephemeral=True
            )  # pragma: no cover

        @self.bot.listen(once=True)
        async def on_ready():
            self.logger.info(
                f"Bot is ready! Logged in as {self.bot.user.name} "
                f"({self.bot.user.id})"
            )  # pragma: no cover
            self.add_tasks()  # pragma: no cover

    def add_tasks(self):
        time_update_legal_cards = datetime.time(hour=7)
        time_update_signup_sheet = datetime.time(hour=8)
        time_update_events = datetime.time(hour=9)
        interval_update_newsfeed = {"hours": 6}

        @tasks.loop(time=time_update_legal_cards)
        async def update_legal_cards():
            self.get_legal_cards_task()  # pragma: no cover

        @tasks.loop(time=time_update_signup_sheet)
        async def update_signup_sheet():
            self.update_signup_sheet_task()  # pragma: no cover

        @tasks.loop(**interval_update_newsfeed)
        async def update_newsfeed():
            await self.get_newsfeed_task()  # pragma: no cover

        @tasks.loop(time=time_update_events)
        async def update_events():
            await self.sync_events_task()   # pragma: no cover

        update_legal_cards.start()
        update_signup_sheet.start()
        update_newsfeed.start()
        update_events.start()
        self.logger.info("Scheduled tasks started.")

    def run(self):
        self.bot.run(self.token)
