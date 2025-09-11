import os
import discord
import json
from datetime import datetime

from .core import fill_sheet, DATA_FOLDER
from .pokemon import get_decklist_png as get_sign_up_sheet

from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE

OUTPUT_CHANNEL_NOT_SET_ERROR = (
    "Tournament output channel is not set for this server."
)
OUTPUT_CHANNEL_NOT_FOUND_ERROR = (
    "Tournament output channel not found. Please set it again."
)
TEST_MESSAGE = "This is a test message from the bot!"
SIGN_UP_SHEET_MISSING_ERROR = (
    "Sign-up sheet is not available. Please try again later."
)

TOURNAMENT_CHANNELS_FILE = f"{DATA_FOLDER}/tournament_channels.json"
SIGN_UP_SHEET_FILE = f"{DATA_FOLDER}/sign_up_sheet.png"


class TournamentBot:
    def load_tournament_channels(self):
        try:
            with open(TOURNAMENT_CHANNELS_FILE, "r") as f:
                self.tournament_channels = json.load(f)
        except Exception as e:
            self.logger.warning(
                f"Error loading {TOURNAMENT_CHANNELS_FILE}: {e}"
            )
            self.tournament_channels = {}

    def save_tournament_channels(self):
        try:
            with open(TOURNAMENT_CHANNELS_FILE, "w") as f:
                json.dump(self.tournament_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving {TOURNAMENT_CHANNELS_FILE}: {e}")

    def add_tournament_commands(self):
        tournament = self.bot.create_group(
            "tournament", "Manage tournament sign-ups"
        )
        standard_tournament = tournament.create_subgroup(
            "pokemon_standard", "Manage Standard tournaments"
        )
        expanded_tournament = tournament.create_subgroup(
            "pokemon_expanded", "Manage Expanded tournaments"
        )

        @standard_tournament.command(
            name="signup_url",
            description=(
                "Sign up for a standard tournament with a limitless url"
            )
        )
        async def signup_url(
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
                str, "Limitless URL of the decklist"
            ),
        ):
            await self.tournament_signup_url(
                ctx, name, pokemon_id, year_of_birth, limitless_url, "standard"
            )  # pragma: no cover

        @expanded_tournament.command(
            name="signup_url",
            description=(
                "Sign up for a expanded tournament with a limitless url"
            )
        )
        async def expanded_signup_url(
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
                str, "Limitless URL of the decklist"
            ),
        ):
            await self.tournament_signup_url(
                ctx, name, pokemon_id, year_of_birth, limitless_url, "expanded"
            )  # pragma: no cover

        @standard_tournament.command(
            name="signup",
            description="Sign up for a standard tournament with a saved deck"
        )
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
            deck_name: str = discord.Option(
                str, "Name of the deck"
            ),
        ):
            await self.tournament_signup(
                ctx, name, pokemon_id, year_of_birth, deck_name, "standard"
            )  # pragma: no cover

        @expanded_tournament.command(
            name="signup",
            description="Sign up for a expanded tournament with a saved deck"
        )
        async def expanded_signup(
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
            deck_name: str = discord.Option(
                str, "Name of the deck"
            ),
        ):
            await self.tournament_signup(
                ctx, name, pokemon_id, year_of_birth, deck_name, "expanded"
            )  # pragma: no cover

        @self.admin_pokemon.command(description="Update the sign-up sheet")
        async def update_signup_sheet(ctx):
            await self.update_signup_sheet(ctx)  # pragma: no cover

        @self.admin_pokemon.command(
            description="Set the output channel for tournament sign-ups"
        )
        async def set_tournament_channel(ctx):
            await self.set_tournament_channel(ctx)  # pragma: no cover

        @self.admin_pokemon.command(
            description="Test output channel for tournament sign-ups"
        )
        async def test_tournament_channel(ctx):
            await self.test_tournament_channel(ctx)  # pragma: no cover

    async def set_tournament_channel(self, ctx):
        channel_id = ctx.channel.id
        self.tournament_channels[str(ctx.guild.id)] = channel_id
        self.save_tournament_channels()
        await ctx.respond(
            f"Tournament output channel set to {ctx.channel.name}!",
            ephemeral=True
        )

    async def test_tournament_channel(self, ctx):
        channel, error = self.get_tournament_channel(str(ctx.guild.id))

        if channel is None:
            await ctx.respond(error, ephemeral=True)
            return

        await channel.send(TEST_MESSAGE)
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

    async def tournament_signup(
        self,
        ctx,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        deck_name: str,
        format: str
    ):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        deck_name = deck_name.strip()

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        deck_data = self.user_decklists.get(user_id, {}).get(deck_name, None)
        if deck_data is None:
            await ctx.respond("Deck not found", ephemeral=True)
            return

        limitless_url = deck_data.get("url")

        if self.legal_cards is None:
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
                SIGN_UP_SHEET_MISSING_ERROR,
                ephemeral=True
            )
            return

        valid = self.validate_decklist_all_formats(deck_data["deck"])

        self.user_decklists[user_id][deck_name].update(
            {
                "last_checked": str(datetime.now().date())
            }
        )
        self.user_decklists[user_id][deck_name].update(valid)

        self.save_user_decklists()

        if valid["standard"]["valid"] is False:
            await ctx.respond(
                f"Decklist is not valid: {valid['standard']['error']}",
                ephemeral=True
            )
            return

        await self.tournament_signup_response(
            ctx, channel, deck_data["deck"], full_name,
            pokemon_id, year_of_birth, limitless_url, format
        )

    async def tournament_signup_response(
        self,
        ctx,
        channel,
        deck_data,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        limitless_url: str,
        format: str
    ):
        output_filename = (
            f"{DATA_FOLDER}/sign_up_sheet_{ctx.guild.id}_{ctx.author.id}.png"
        )

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
                f"New tournament signup:\n- Format: {format}\n"
                f"- Name: {full_name} ({author})\n"
                f"- Pokémon ID: {pokemon_id}\n"
                f"- Year of Birth: {year_of_birth}\n"
                f"- Decklist: {limitless_url}"
            ),
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        await ctx.respond(
            "Tournament signup has been processed!",
            ephemeral=True,
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        os.remove(output_filename)  # Clean up the temporary file

    async def tournament_signup_url(
        self,
        ctx,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        limitless_url: str,
        format: str
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
                SIGN_UP_SHEET_MISSING_ERROR,
                ephemeral=True
            )
            return

        result, deck_data, error = self.do_decklist_check(limitless_url)

        if error is not None:
            await ctx.respond(
                f"Error checking decklist: {error}", ephemeral=True
            )
            return

        if result[format]["valid"] is False:
            await ctx.respond(
                f"Deck is not valid: {result[format]['error']}",
                ephemeral=True
            )
            return

        await self.tournament_signup_response(
            ctx, channel, deck_data, full_name, pokemon_id,
            year_of_birth, limitless_url, format
        )

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

    def do_update_sheet(self) -> Exception | None:
        t = CustomThread(get_sign_up_sheet, kwargs={
            "output_filename": SIGN_UP_SHEET_FILE
        })
        t.start()
        _, error = t.join()
        return error

    def check_sign_up_sheet(self) -> bool:
        return os.path.exists(SIGN_UP_SHEET_FILE)
