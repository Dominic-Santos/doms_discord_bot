import os
import discord
import json

from .limitless import get_decklist_from_url
from .core import validate_decklist, fill_sheet
from .pokemon import get_decklist_png as get_sign_up_sheet

from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE

OUTPUT_CHANNEL_NOT_SET_ERROR = (
    "Tournament output channel is not set for this server."
)
OUTPUT_CHANNEL_NOT_FOUND_ERROR = (
    "Tournament output channel not found. Please set it again."
)


class DecklistBot:
    def load_tournament_channels(self):
        try:
            with open("tournament_channels.json", "r") as f:
                self.tournament_channels = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading tournament_channels.json: {e}")
            self.tournament_channels = {}

    def save_tournament_channels(self):
        try:
            with open("tournament_channels.json", "w") as f:
                json.dump(self.tournament_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving tournament_channels.json: {e}")

    def add_decklist_commands(self):
        tournament = self.bot.create_group(
            "tournament", "Manage tournament sign-ups"
        )
        decklist = self.bot.create_group("decklist", "Manage your deck")

        @decklist.command(description="Check your decklist is standard legal")
        async def check(
            ctx,
            limitless_url: discord.Option(
                str, "Limitless URL of the decklist"
            ),  # type: ignore
        ):
            await self.decklist_check(ctx, limitless_url)  # pragma: no cover

        @tournament.command(description="Sign up for a tournament")
        async def signup(
            ctx,
            name: discord.Option(
                str, "Full name of the player"
            ),  # type: ignore
            pokemon_id: discord.Option(
                int, "Pokemon ID of the player"
            ),  # type: ignore
            year_of_birth: discord.Option(
                int, "Year of birth of the player"
            ),  # type: ignore
            limitless_url: str = discord.Option(
                str,
                "Limitless URL of the decklist"
            ),
        ):
            await self.tournament_signup(
                ctx, name, pokemon_id, year_of_birth, limitless_url
            )  # pragma: no cover

        @self.admin.command(description="Update the sign-up sheet")
        async def update_signup_sheet(ctx):
            await self.update_signup_sheet(ctx)  # pragma: no cover

        @self.admin.command(
            description="Set the output channel for tournament sign-ups"
        )
        async def set_tournament_channel(ctx):
            await self.set_tournament_channel(ctx)  # pragma: no cover

        @self.admin.command(
            description="Test output channel for tournament sign-ups"
        )
        async def test_tournament_channel(ctx):
            await self.test_tournament_channel(ctx)  # pragma: no cover

    async def set_tournament_channel(self, ctx):
        channel_id = ctx.channel.id
        self.tournament_channels[str(ctx.guild.id)] = channel_id
        self.save_tournament_channels()
        await ctx.respond(
            f"Output channel set to {ctx.channel.name}!",
            ephemeral=True
        )

    async def test_tournament_channel(self, ctx):
        channel, error = self.get_tournament_channel(str(ctx.guild.id))

        if channel is None:
            await ctx.respond(error, ephemeral=True)
            return

        await channel.send("This is a test message from the bot!")
        await ctx.respond(
            "Test message sent to the output channel!",
            ephemeral=True
        )

    def get_tournament_channel(self, guild_id: str) -> tuple[
        discord.TextChannel | None, str
    ]:
        if guild_id not in self.tournament_channels:
            return None, OUTPUT_CHANNEL_NOT_SET_ERROR

        channel_id = self.tournament_channels[guild_id]
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel, ""

        return None, OUTPUT_CHANNEL_NOT_FOUND_ERROR

    async def decklist_check(self, ctx, deck):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        valid, _, error = self.do_decklist_check(deck)
        if not valid:
            await ctx.respond(
                f"Decklist is not valid: {error}",
                ephemeral=True
            )
            return
        await ctx.respond("Decklist is valid!", ephemeral=True)

    def do_decklist_check(self, limitless_url: str) -> tuple[bool, dict, str]:
        valid = self.check_limitless_url(limitless_url)
        if not valid:
            return False, {}, "Invalid Limitless URL."
        t = CustomThread(get_decklist_from_url, args=(limitless_url,))
        t.start()
        deck_data, error = t.join()
        valid, error = validate_decklist(deck_data, self.legal_cards)
        return valid, deck_data, error

    async def tournament_signup(
        self,
        ctx,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        limitless_url: str
    ):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        if not self.legal_cards:
            await ctx.respond(
                "Legal cards are not loaded. Please try again later.",
                ephemeral=True
            )
            return

        channel, error = self.get_tournament_channel(str(ctx.guild.id))
        if channel is None:
            await ctx.respond(error, ephemeral=True)
            return

        if not self.check_sign_up_sheet():
            await ctx.respond(
                "Sign-up sheet is not available. Please try again later.",
                ephemeral=True
            )
            return

        valid, deck_data, error = self.do_decklist_check(limitless_url)
        if not valid:
            await ctx.respond(
                f"Decklist is not valid: {error}",
                ephemeral=True
            )
            return

        output_filename = f"sign_up_sheet_{ctx.guild.id}_{ctx.author.id}.png"

        fill_sheet(
            player={
                "name": full_name,
                "id": str(pokemon_id),
                "year_of_birth": str(year_of_birth)
            },
            cards=deck_data,
            output_filename=output_filename
        )

        author = ctx.author.mention

        await channel.send(
            (
                f"New tournament signup:\n- Name: {full_name} ({author})\n"
                f"- Pokémon ID: {pokemon_id}\n- Year of Birth: {year_of_birth}"
                f"\n- Decklist: {limitless_url}"
            ),
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        await ctx.respond(
            "Tournament signup has been processed!",
            ephemeral=True,
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        os.remove(output_filename)  # Clean up the temporary file

    async def update_signup_sheet(self, ctx):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        error = self.do_update_sheet()
        if error is None:
            msg = "Sheet has been updated!"
        else:
            msg = f"Failed to update sheet {error}"
        await ctx.respond(msg, ephemeral=True)

    def update_signup_sheet_task(self):
        self.logger.info("Updating sign-up sheet...")

        if self.maintenance:
            self.logger.info(
                "Won't update sign-up sheet, Maintenance mode is active"
            )
            return

        error = self.do_update_sheet()
        if error is None:
            self.logger.info("Sign-up sheet updated successfully.")
        else:
            self.logger.error(f"Failed up update sign-up sheet {error}")

    def do_update_sheet(self):
        t = CustomThread(get_sign_up_sheet)
        t.start()
        _, error = t.join()
        return error

    def check_limitless_url(self, url: str) -> tuple[bool]:
        clean = url.strip("https://").strip("http://")
        if clean.startswith("my.limitlesstcg.com/builder?i="):
            return True
        return False

    def check_sign_up_sheet(self):
        return os.path.exists("sign_up_sheet.png")
