import datetime
import discord
import json

from discord.ext import tasks
from threading import Thread

from .decklist.limitless import get_decklist_from_url
from .decklist.core import validate_decklist, load_card_database
from .decklist.pkmncards import get_legal_cards

from .helpers import create_logger


class CustomThread(Thread):
    def __init__(self, target, args=[], kwargs={}):
        super().__init__(target=target, args=args, **kwargs)
        self.daemon = True  # Set the thread as a daemon thread
        self.return_value = None
    
    def run(self):
        self.return_value = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.return_value

class Bot:
    def __init__(self, token):
        self.bot = discord.Bot()
        self.token = token
        self.logger = create_logger("decklist_bot", filename="logs/bot.log")

        self.load_legal_cards()
        self.load_output_channels()
        self.add_commands()
        self.add_tasks()
    
    def load_legal_cards(self):
        try:
            legal_pokemon, legal_trainers, legal_energies = load_card_database()
            self.legal_cards = {
                "pokemon": legal_pokemon,
                "trainers": legal_trainers,
                "energies": legal_energies
            }
        except Exception as e:
            self.logger.info(f"Error loading legal cards database: {e}")
            self.legal_cards = None

    def load_output_channels(self):
        try:
            with open("output_channels.json", "r") as f:
                self.output_channels = json.load(f)
        except Exception as e:
            self.logger.info(f"Error loading output_channels.json: {e}")
            self.output_channels = {}

    def save_output_channels(self):
        try:
            with open("output_channels.json", "w") as f:
                json.dump(self.output_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving output_channels.json: {e}")

    def add_commands(self):
        decklist = self.bot.create_group("decklist", "Manage your deck")
        legalcards = self.bot.create_group("legalcards", "Manage your legal cards")
        output = self.bot.create_group("output", "Manage output channels")

        @decklist.command(description="Check your decklist is standard legal")
        async def check(ctx, deck: str):
            await self.decklist_check(ctx, deck)

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

        @tasks.loop(time=time_update_legal_cards)
        async def update_legal_cards():
            self.logger.info("Updating legal cards...")
            self.do_get_legal_cards()
            self.logger.info("Legal cards updated successfully.")

        update_legal_cards.start()

    async def set_output_channel(self, ctx):
        channel_id = ctx.channel.id
        self.output_channels[str(ctx.guild.id)] = channel_id
        self.save_output_channels()
        await ctx.respond(f"Output channel set to {ctx.channel.name}!", ephemeral=True)

    async def test_output_channel(self, ctx):
        if str(ctx.guild.id) not in self.output_channels:
            await ctx.respond("Output channel is not set for this server. Use `/output set` to set it.", ephemeral=True)
            return
        
        channel_id = self.output_channels[str(ctx.guild.id)]
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send("This is a test message from the bot!")
        else:
            await ctx.respond("Output channel not found. Please set it again.", ephemeral=True)
            return
        await ctx.respond("Test message sent to the output channel!", ephemeral=True)

    async def decklist_check(self, ctx, deck):
        await ctx.defer(ephemeral=True)
        t = CustomThread(get_decklist_from_url, args=(deck,))
        t.start()
        deck_data = t.join()
        valid, error = validate_decklist(deck_data, self.legal_cards)
        if not valid:
            await ctx.respond(f"Decklist is not valid: {error}", ephemeral=True)
            return
        await ctx.respond("Decklist is valid!", ephemeral=True)

    async def get_legal_cards(self, ctx):
        await ctx.defer(ephemeral=True)
        self.do_get_legal_cards()
        await ctx.respond("Legal cards list has been updated!", ephemeral=True)

    def do_get_legal_cards(self):
        t = CustomThread(get_legal_cards)
        t.start()
        t.join()
        self.load_legal_cards()

    def run(self):
        self.bot.run(self.token)
