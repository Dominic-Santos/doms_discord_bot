import os
import discord
import json
from datetime import datetime

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
TEST_MESSAGE = "This is a test message from the bot!"
SIGN_UP_SHEET_MISSING_ERROR = (
    "Sign-up sheet is not available. Please try again later."
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

    def load_user_decklists(self):
        try:
            with open("user_decklists.json", "r") as f:
                self.user_decklists = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading user_decklists.json: {e}")
            self.user_decklists = {}

    def save_user_decklists(self):
        try:
            with open("user_decklists.json", "w") as f:
                json.dump(self.user_decklists, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving user_decklists.json: {e}")

    def add_decklist_commands(self):
        tournament = self.bot.create_group(
            "tournament", "Manage tournament sign-ups"
        )
        decklist = self.bot.create_group("decklist", "Manage your deck")

        @decklist.command(description="Check a decklist is standard legal")
        async def check_url(
            ctx,
            limitless_url: discord.Option(
                str, "Limitless URL of the decklist"
            ),  # type: ignore
        ):
            await self.decklist_check_url(
                ctx, limitless_url
            )  # pragma: no cover

        @decklist.command(description="Check a decklist is standard legal")
        async def check(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_check(ctx, name)  # pragma: no cover

        @decklist.command(description="Create a decklist")
        async def create(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
            limitless_url: discord.Option(
                str, "Limitless URL of the decklist"
            ),  # type: ignore
        ):
            await self.decklist_create(
                ctx, name, limitless_url
            )  # pragma: no cover

        @decklist.command(description="Create a decklist")
        async def delete(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_delete(ctx, name)  # pragma: no cover

        @decklist.command(name="list", description="Create a decklist")
        async def list_all(ctx):
            await self.decklist_list(ctx)  # pragma: no cover

        @decklist.command(description="Create a decklist")
        async def info(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_info(ctx, name)  # pragma: no cover

        @tournament.command(
            description="Sign up for a tournament with a limitless url"
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
                ctx, name, pokemon_id, year_of_birth, limitless_url
            )  # pragma: no cover

        @tournament.command(
            description="Sign up for a tournament with a saved decklist"
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
                ctx, name, pokemon_id, year_of_birth, deck_name
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

    async def decklist_info(self, ctx, name: str):
        user_id = str(ctx.author.id)
        name = name.strip()

        deck_data = self.user_decklists.get(user_id, {}).get(name, None)
        if deck_data is None:
            await ctx.respond("Deck not found", ephemeral=True)
            return

        deck_info = f"{name}\nStandard Legal: "
        if deck_data["valid"]:
            deck_info += ":white_check_mark:"
        else:
            deck_info += ":x:"

        deck_info += f" ({deck_data['last_checked']})"

        if not deck_data["valid"]:
            deck_info += f"\nError: {deck_data['error']}"

        if "deck" in deck_data:
            if (
                "pokemon" in deck_data["deck"] and
                len(deck_data["deck"]["pokemon"]) > 0
            ):
                deck_info += "\nPokemon:\n"
                sorted_pokemon = sorted(
                    deck_data["deck"]["pokemon"], key=lambda x: x["name"]
                )
                deck_info += "\n".join(
                    f"\t{p['quantity']}x {p['name']} {p['set']}-{p['number']}"
                    for p in sorted_pokemon
                )
            if (
                "trainers" in deck_data["deck"] and
                len(deck_data["deck"]["trainers"].keys()) > 0
            ):
                deck_info += "\nTrainers:\n"
                trainers = deck_data["deck"]["trainers"]
                sorted_trainers = sorted(trainers.keys())
                deck_info += "\n".join(
                    f"\t{trainers[t]}x {t}"
                    for t in sorted_trainers
                )
            if (
                "energies" in deck_data["deck"] and
                len(deck_data["deck"]["energies"].keys()) > 0
            ):
                deck_info += "\nEnergies:\n"
                energies = deck_data["deck"]["energies"]
                sorted_energies = sorted(energies.keys())
                deck_info += "\n".join(
                    f"\t{energies[t]}x {t}"
                    for t in sorted_energies
                )

        await ctx.respond(deck_info, ephemeral=True)

    async def decklist_delete(self, ctx, name: str):
        user_id = str(ctx.author.id)
        name = name.strip()

        if user_id in self.user_decklists:
            if name in self.user_decklists[user_id]:
                del self.user_decklists[user_id][name]
                await ctx.respond("Deck was deleted", ephemeral=True)
                self.save_user_decklists()
                return

        await ctx.respond("Deck not found", ephemeral=True)

    async def decklist_list(self, ctx):
        user_id = str(ctx.author.id)
        user_decks = self.user_decklists.get(user_id, {})

        if len(user_decks.keys()) == 0:
            await ctx.respond("You have no saved decks")
            return

        decks = "\n".join(f"\t{deck}" for deck in sorted(user_decks.keys()))
        await ctx.respond(f"Your decks:\n{decks}")

    async def decklist_check(self, ctx, name: str):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        name = name.strip()

        valid, error = self.do_user_decklist_check(user_id, name)
        if valid:
            result = "valid!"
        else:
            result = f"not valid! {error}"

        await ctx.respond(
            f"Decklist is {result}",
            ephemeral=True
        )

    async def decklist_create(self, ctx, name: str, limitless_url: str):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        name = name.strip()
        if user_id not in self.user_decklists:
            self.user_decklists[user_id] = {}

        self.user_decklists[user_id][name] = {
            "url": limitless_url
        }

        valid, error = self.do_user_decklist_check(user_id, name)
        if valid:
            result = "valid!"
        else:
            result = f"not valid! {error}"

        await ctx.respond(
            f"Deck saved, decklist is {result}",
            ephemeral=True
        )
        self.save_user_decklists()

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

    async def decklist_check_url(self, ctx, deck_url: str):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        valid, _, error = self.do_decklist_check(deck_url)
        if not valid:
            await ctx.respond(
                f"Decklist is not valid: {error}",
                ephemeral=True
            )
            return
        await ctx.respond("Decklist is valid!", ephemeral=True)

    def do_user_decklist_check(
        self, user_id: str, deck_name: str
    ) -> tuple[bool, str]:
        deck_data = self.user_decklists.get(
            user_id, {}
        ).get(deck_name, None)

        if deck_data is None:
            return False, "Deck not found"

        decklist_url = deck_data["url"]

        valid, deck_data, error = self.do_decklist_check(decklist_url)
        self.user_decklists[user_id][deck_name].update(
            {
                "valid": valid,
                "deck": deck_data,
                "error": error,
                "last_checked": str(datetime.now().date())
            }
        )
        self.save_user_decklists()
        return valid, error

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
        deck_name: str
    ):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        deck_name = deck_name.strip()

        deck_data = self.user_decklists.get(user_id, {}).get(deck_name, None)
        if deck_data is None:
            await ctx.respond("Deck not found", ephemeral=True)
            return

        limitless_url = deck_data.get("url")

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

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

        valid, error = await self.tournament_signup_response(
            ctx, channel, full_name, pokemon_id, year_of_birth, limitless_url
        )

        self.user_decklists[user_id][deck_name].update(
            {
                "valid": valid,
                "error": error,
                "last_checked": str(datetime.now().date())
            }
        )
        self.save_user_decklists()

    async def tournament_signup_response(
        self,
        ctx,
        channel,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        limitless_url: str,
    ) -> tuple[bool, str]:
        valid, deck_data, error = self.do_decklist_check(limitless_url)
        if not valid:
            await ctx.respond(
                f"Decklist is not valid: {error}",
                ephemeral=True
            )
            return valid, error

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
        return True, ""

    async def tournament_signup_url(
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
                SIGN_UP_SHEET_MISSING_ERROR,
                ephemeral=True
            )
            return

        valid, error = await self.tournament_signup_response(
            ctx, channel, full_name, pokemon_id, year_of_birth, limitless_url
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
        t = CustomThread(get_sign_up_sheet)
        t.start()
        _, error = t.join()
        return error

    def check_limitless_url(self, url: str) -> tuple[bool]:
        clean = url.strip("https://").strip("http://")
        if clean.startswith("my.limitlesstcg.com/builder?i="):
            return True
        return False

    def check_sign_up_sheet(self) -> bool:
        return os.path.exists("sign_up_sheet.png")
