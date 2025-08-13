import datetime
import discord

from discord.ext import tasks

from .helpers import create_logger
from .bot_decklist import DecklistBot
from .bot_legalcards import LegalCardsBot
from .bot_newsfeed import NewsfeedBot


class Bot(DecklistBot, LegalCardsBot, NewsfeedBot):
    def __init__(self, token: str, maintenance_mode: bool, password: str):
        self.bot = discord.Bot()
        self.token = token
        self.maintenance = maintenance_mode
        self.password = password
        self.logger = create_logger("decklist_bot", filename="logs/bot.log")

        self.load_legal_cards()
        self.load_output_channels()
        self.load_newsfeed_channels()
        self.add_commands()
    
    def add_commands(self):
        decklist = self.bot.create_group("decklist", "Manage your deck")
        newsfeed = self.bot.create_group("newsfeed", "Manage newsfeed posts")
        tournament = self.bot.create_group("tournament", "Manage tournament sign-ups")
        admin = self.bot.create_group("admin", "Admin commands")

        @decklist.command(description="Check your decklist is standard legal")
        async def check(ctx, limitless_url: discord.Option(str, "Limitless URL of the decklist")):
            await self.decklist_check(ctx, limitless_url)  # pragma: no cover

        @tournament.command(description="Sign up for a tournament")
        async def signup(
            ctx,
            name: discord.Option(str, "Full name of the player"),
            pokemon_id: discord.Option(int, "Pokemon ID of the player"),
            year_of_birth: discord.Option(int, "Year of birth of the player"),
            limitless_url: discord.Option(str, "Limitless URL of the decklist"),
        ):
            await self.tournament_signup(ctx, name, pokemon_id, year_of_birth, limitless_url)  # pragma: no cover

        @admin.command(description="Update the sign-up sheet")
        async def update_signup_sheet(ctx):
            await self.update_signup_sheet(ctx)  # pragma: no cover

        @admin.command(description="Sync the legal cards list for deck validation")
        async def update_legal_cards(ctx):
            await self.get_legal_cards(ctx)  # pragma: no cover

        @admin.command(description="Set the output channel for tournament sign-ups")
        async def set_output_channel(ctx):
            await self.set_output_channel(ctx)  # pragma: no cover

        @admin.command(description="Test output channel for tournament sign-ups")
        async def test_output_channel(ctx):
            await self.test_output_channel(ctx)  # pragma: no cover

        @newsfeed.command(description="Set the newsfeed channel")
        async def set_channel(ctx):
            await self.set_newsfeed_channel(ctx)  # pragma: no cover

        @newsfeed.command(description="Check for newsfeed updates")
        async def update(ctx):
            await self.get_newsfeed(ctx)  # pragma: no cover

        @self.bot.command(description="Get information about the bot")
        async def about(ctx):
            await ctx.respond("This is a Discord bot built for managing Pokémon TCG events and News.\n\nIt can validate decklists, manage tournament sign-ups, and provide news updates from PokéBeach.\n\nCreated by Dominic Santos (dominatordom8125 on Discord) ", ephemeral=True)  # pragma: no cover

        @self.bot.listen(once=True)
        async def on_ready():
            self.logger.info(f"Bot is ready! Logged in as {self.bot.user.name} ({self.bot.user.id})")  # pragma: no cover
            self.add_tasks()  # pragma: no cover

    def add_tasks(self):
        time_update_legal_cards = datetime.time(hour=7)
        time_update_signup_sheet = datetime.time(hour=8)
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

        update_legal_cards.start()
        update_signup_sheet.start()
        update_newsfeed.start()
        self.logger.info("Scheduled tasks started.")

    def run(self):
        self.bot.run(self.token)
