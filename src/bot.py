import datetime
import discord

from discord.ext import tasks

from .decklist.limitless import get_decklist_from_url
from .decklist.core import validate_decklist, load_card_database
from .decklist.pkmncards import get_legal_cards

from .helpers import create_logger
from .bot_decklist import DecklistBot
from .bot_legalcards import LegalCardsBot


class Bot(DecklistBot, LegalCardsBot):
    def __init__(self, token):
        self.bot = discord.Bot()
        self.token = token
        self.logger = create_logger("decklist_bot", filename="logs/bot.log")

        self.load_legal_cards()
        self.load_output_channels()
        self.add_commands()
        self.add_tasks()
    
    def add_commands(self):
        decklist = self.bot.create_group("decklist", "Manage your deck")
        legalcards = self.bot.create_group("legalcards", "Manage your legal cards")
        output = self.bot.create_group("output", "Manage output channels")

        @decklist.command(description="Check your decklist is standard legal")
        async def check(ctx, limitless_url: str):
            await self.decklist_check(ctx, limitless_url)

        @decklist.command(description="Sign up for a tournament")
        async def signup(ctx, full_name: str, pokemon_id: int, year_of_birth: int, limitless_url: str):
            await self.tournament_signup(ctx, full_name, pokemon_id, year_of_birth, limitless_url)

        @decklist.command(description="Update the sign-up sheet")
        async def update_sheet(ctx):
            await self.update_signup_sheet(ctx)

        @legalcards.command(description="Sync the legal cards list")
        async def sync(ctx):
            await self.get_legal_cards(ctx)

        @output.command(description="Set the output channel for the bot")
        async def set(ctx):
            await self.set_output_channel(ctx)

        @output.command(description="Test output channel")
        async def test(ctx):
            await self.test_output_channel(ctx)

        @self.bot.listen(once=True)
        async def on_ready():
            self.logger.info(f"Bot is ready! Logged in as {self.bot.user.name} ({self.bot.user.id})")

    def add_tasks(self):
        time_update_legal_cards = datetime.time(hour=7)
        time_update_signup_sheet = datetime.time(hour=8)

        @tasks.loop(time=time_update_legal_cards)
        async def update_legal_cards():
            self.get_legal_cards_task()

        @tasks.loop(time=time_update_signup_sheet)
        async def update_signup_sheet():
            self.update_signup_sheet_task()

        update_legal_cards.start()
        update_signup_sheet.start()
        self.logger.info("Scheduled tasks started.")

    def run(self):
        self.bot.run(self.token)
