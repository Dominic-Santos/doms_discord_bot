import os
import discord
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from .core import fill_sheet, DATA_FOLDER
from .pokemon import get_decklist_png as get_sign_up_sheet

from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE
from .modals import CommandModal

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
TOURNAMENTS_FILE = f"{DATA_FOLDER}/tournaments.json"
TOURNAMENT_SIGNUPS_FILE = f"{DATA_FOLDER}/tournament_signups.json"
SIGN_UP_SHEET_FILE = f"{DATA_FOLDER}/sign_up_sheet.png"


class TournamentSelectView(discord.ui.View):  # pragma: no cover
    def __init__(self, tournaments: dict):
        super().__init__()
        
        # Create select options for tournaments
        options = [
            discord.SelectOption(
                label=tournament_data.get("name", tournament_id)[:100],
                value=tournament_id,
                description=f"Expires: {tournament_data.get('expires_at', 'Unknown')}"[:100]
            )
            for tournament_id, tournament_data in tournaments.items()
        ]
        
        if options:
            self.select.options = options
        else:
            self.select.disabled = True

    @discord.ui.select(
        placeholder="Select a tournament",
        min_values=1,
        max_values=1
    )
    async def select(self, select: discord.ui.Select, interaction: discord.Interaction):
        # Store selected tournament in the view
        self.selected_tournament_id = select.values[0]
        self.stop()


class TournamentSignupView(discord.ui.View):  # pragma: no cover
    def __init__(self, tournament_bot, open_tournaments, user_id):
        super().__init__(timeout=120)
        self.tournament_bot = tournament_bot
        self.open_tournaments = open_tournaments
        self.user_id = user_id

        options = [
            discord.SelectOption(
                label=data.get("name", tournament_id)[:100],
                value=tournament_id,
                description=f"Expires: {data.get('expires_at', 'Unknown')}"[:100],
            )
            for tournament_id, data in open_tournaments.items()
        ]
        select = discord.ui.Select(
            placeholder="Select the tournament",
            options=options,
        )

        async def select_callback(interaction):
            tournament_id = select.values[0]
            await self.show_deck_choice(interaction, tournament_id)

        select.callback = select_callback
        self.add_item(select)

    async def show_deck_choice(self, interaction, tournament_id):
        saved_decks = self.tournament_bot.user_decklists.get(
            self.user_id, {}
        )
        if not saved_decks:
            await interaction.response.send_modal(
                self.tournament_bot.create_signup_modal(tournament_id)
            )
            self.stop()
            return

        view = SavedDeckSelectView(
            self.tournament_bot,
            tournament_id,
            saved_decks,
        )
        await interaction.response.edit_message(
            content="Select a saved deck, or choose to enter a deck URL:",
            view=view,
        )
        self.stop()


class SavedDeckSelectView(discord.ui.View):  # pragma: no cover
    def __init__(self, tournament_bot, tournament_id, saved_decks):
        super().__init__(timeout=120)
        self.tournament_bot = tournament_bot
        self.tournament_id = tournament_id

        options = [
            discord.SelectOption(
                label="Use a deck URL",
                value="__deck_url__",
                description="Enter a Limitless URL manually",
            ),
        ] + [
            discord.SelectOption(label=name[:100], value=name)
            for name in saved_decks
        ]
        select = discord.ui.Select(
            placeholder="Select a deck",
            options=options[:25],
        )

        async def select_callback(interaction):
            selected = select.values[0]
            deck_url = None
            if selected != "__deck_url__":
                deck_url = saved_decks[selected].get("url")
            await interaction.response.send_modal(
                self.tournament_bot.create_signup_modal(
                    self.tournament_id,
                    deck_url,
                )
            )
            self.stop()

        select.callback = select_callback
        self.add_item(select)


class TournamentBot:
    def get_tournament_signup_status(
        self,
        now: Optional[datetime] = None,
    ) -> tuple[bool, Optional[str]]:
        if now is None:
            now = datetime.now()

        expires_at = self.tournament_signup_expires_at
        if not expires_at:
            return False, "no tournaments are being held at this moment"

        try:
            expire_datetime = datetime.fromisoformat(expires_at)
        except ValueError:
            self.logger.error(
                "Invalid tournament signup expiry datetime in config: "
                f"{expires_at}"
            )
            return False, "no tournaments are being held at this moment"

        if now <= expire_datetime:
            return True, None

        if now - expire_datetime <= timedelta(days=1):
            return False, "tournament sign ups are closed"

        return False, "no tournaments are being held at this moment"

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

    def load_tournaments(self):
        try:
            with open(TOURNAMENTS_FILE, "r") as f:
                data = json.load(f)
                self.tournaments = data.get("tournaments", {})
        except Exception as e:
            self.logger.warning(
                f"Error loading {TOURNAMENTS_FILE}: {e}"
            )
            self.tournaments = {}

    def save_tournaments(self):
        try:
            with open(TOURNAMENTS_FILE, "w") as f:
                json.dump({"tournaments": self.tournaments}, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving {TOURNAMENTS_FILE}: {e}")

    def load_tournament_signups(self):
        try:
            with open(TOURNAMENT_SIGNUPS_FILE, "r") as f:
                data = json.load(f)
                self.tournament_signups = data.get("signups", {})
        except Exception as e:
            self.logger.warning(
                f"Error loading {TOURNAMENT_SIGNUPS_FILE}: {e}"
            )
            self.tournament_signups = {}

    def save_tournament_signups(self):
        try:
            with open(TOURNAMENT_SIGNUPS_FILE, "w") as f:
                json.dump({"signups": self.tournament_signups}, f, indent=4)
        except Exception as e:
            self.logger.error(
                f"Error saving {TOURNAMENT_SIGNUPS_FILE}: {e}"
            )

    def get_open_tournaments(
        self,
        now: Optional[datetime] = None,
    ) -> dict:
        """Get all tournaments that are currently open."""
        if now is None:
            now = datetime.now()

        open_tournaments = {}
        for tournament_id, tournament_data in self.tournaments.items():
            try:
                expire_datetime = datetime.fromisoformat(
                    tournament_data.get("expires_at", "")
                )
                if now <= expire_datetime:
                    open_tournaments[tournament_id] = tournament_data
            except ValueError:
                self.logger.warning(
                    f"Invalid tournament expiry datetime for {tournament_id}: "
                    f"{tournament_data.get('expires_at')}"
                )
                continue

        return open_tournaments

    async def get_tournament_selection(
        self,
        ctx,
        open_tournaments: dict
    ) -> Optional[str]:
        """Prompt user to select a tournament from dropdown. Returns tournament_id or None."""
        if len(open_tournaments) == 1:
            # Auto-select if only one tournament is open
            return list(open_tournaments.keys())[0]
        
        if len(open_tournaments) == 0:
            return None

        # Create and send dropdown
        view = TournamentSelectView(open_tournaments)
        await ctx.respond(
            "Please select a tournament to sign up for:",
            view=view,
            ephemeral=True
        )
        
        # Wait for selection (30 second timeout)
        try:
            await view.wait()
            return getattr(view, 'selected_tournament_id', None)
        except Exception as e:
            self.logger.error(f"Error in tournament selection: {e}")
            return None

    def add_tournament_commands(self):  # pragma: no cover
        tournament = self.bot.create_group(
            "tournament", "Manage tournament sign-ups"
        )

        @tournament.command(description="Sign up for a tournament")
        async def signup(ctx):  # pragma: no cover
            open_tournaments = self.get_open_tournaments()
            if not open_tournaments:
                await ctx.respond(
                    "No tournaments are open at this moment.",
                    ephemeral=True,
                )
                return

            await ctx.respond(
                "Select the tournament you are signing up for:",
                view=TournamentSignupView(
                    self,
                    open_tournaments,
                    str(ctx.author.id),
                ),
                ephemeral=True,
            )

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

        @self.admin_pokemon.command(
            description="List tournament sign-ups as CSV text"
        )
        async def list_signups(ctx):
            await self.export_tournament_signups(ctx)  # pragma: no cover

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

    async def export_tournament_signups(self, ctx):
        await ctx.defer(ephemeral=True)
        guild_id = str(ctx.guild.id)
        guild_signups = self.tournament_signups.get(guild_id, [])

        if not guild_signups:
            await ctx.respond(
                "No tournament sign-ups to list.",
                ephemeral=True
            )
            return

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "tournament_name",
            "format",
            "full_name",
            "pokemon_id",
            "year_of_birth",
        ])

        for signup in sorted(
            guild_signups,
            key=lambda item: (
                self.tournaments.get(item.get("tournament_id"), {}).get(
                    "name",
                    item.get("tournament_id", "Unknown"),
                ).lower(),
                str(item.get("full_name", "")).lower(),
            ),
        ):
            tournament_id = signup.get("tournament_id")
            tournament_name = self.tournaments.get(tournament_id, {}).get(
                "name",
                tournament_id or "Unknown",
            )
            writer.writerow([
                tournament_name,
                signup.get("format", "Unknown"),
                signup.get("full_name", "Unknown"),
                signup.get("pokemon_id", "Unknown"),
                signup.get("year_of_birth", "Unknown"),
            ])

        formatted_output = "```csv\n" + output.getvalue().rstrip() + "\n```"
        await ctx.respond(
            formatted_output,
            ephemeral=True,
        )

    def record_tournament_signup(
        self,
        guild_id: int,
        user_id: int,
        full_name: str,
        pokemon_id: int,
        year_of_birth: int,
        limitless_url: str,
        format: str,
        tournament_id: Optional[str] = None,
    ):
        guild_key = str(guild_id)
        if guild_key not in self.tournament_signups:
            self.tournament_signups[guild_key] = []

        updated_signup = {
            "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
            "format": format,
            "full_name": full_name,
            "pokemon_id": pokemon_id,
            "year_of_birth": year_of_birth,
            "limitless_url": limitless_url,
            "discord_user_id": str(user_id),
            "tournament_id": tournament_id
        }

        for i, signup in enumerate(self.tournament_signups[guild_key]):
            same_pokemon = str(signup.get("pokemon_id")) == str(pokemon_id)
            same_tournament = str(signup.get("tournament_id") or "") == str(tournament_id or "")
            if same_pokemon and same_tournament:
                self.tournament_signups[guild_key][i] = updated_signup
                self.save_tournament_signups()
                return

        self.tournament_signups[guild_key].append(updated_signup)
        self.save_tournament_signups()

    def create_signup_modal(self, tournament_id, deck_url=None):
        return CommandModal(
            "Tournament Sign-up",
            [
                ("name", "Full name", "Ash Ketchum", str),
                ("pokemon_id", "Pokemon ID", "123456", int),
                ("year_of_birth", "Year of birth", "1990", int),
                (
                    "limitless_url",
                    "Limitless deck URL",
                    "https://limitlesstcg.com/...",
                    str,
                    deck_url,
                ),
            ],
            lambda modal_ctx, values: self.tournament_signup_url(
                modal_ctx,
                values["name"],
                values["pokemon_id"],
                values["year_of_birth"],
                values["limitless_url"],
                tournament_id,
            ),
            self.logger,
        )

    def get_tournament_channel(self, guild_id: str) -> tuple[
        Optional[discord.TextChannel], str
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
        tournament_id: Optional[str] = None,
    ):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        deck_name = deck_name.strip()

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        # Check if tournament_id is provided, otherwise get open tournaments
        open_tournaments = self.get_open_tournaments()
        if not open_tournaments:
            await ctx.respond(
                "No tournaments are open at this moment.",
                ephemeral=True
            )
            return

        # If multiple tournaments are open and none specified, show dropdown
        if tournament_id is None:
            selected_tournament_id = await self.get_tournament_selection(
                ctx, open_tournaments
            )
            if selected_tournament_id is None:
                await ctx.respond(
                    "No tournament selected.",
                    ephemeral=True
                )
                return
            tournament_id = selected_tournament_id

        if tournament_id not in open_tournaments:
            await ctx.respond(
                "Selected tournament is not open.",
                ephemeral=True
            )
            return

        # Get format from tournament data
        tournament_data = self.tournaments.get(tournament_id, {})
        format = tournament_data.get("format", "standard")

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

        if valid[format]["valid"] is False:
            log_text = (
                f"Decklist for user {full_name} failed validation: "
                f"{valid[format]['error']}"
            )
            self.logger.info(log_text)
            await ctx.respond(
                f"Decklist is not valid: {valid[format]['error']}",
                ephemeral=True
            )
            return

        await self.tournament_signup_response(
            ctx, channel, deck_data["deck"], full_name,
            pokemon_id, year_of_birth, limitless_url, format, tournament_id
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
        format: str,
        tournament_id: Optional[str] = None,
    ):
        output_filename = (
            f"{DATA_FOLDER}/sign_up_sheet_{ctx.guild.id}_{ctx.author.id}.png"
        )

        fill_sheet(
            sheet_location=SIGN_UP_SHEET_FILE,
            player={
                "name": full_name,
                "id": str(pokemon_id),
                "year_of_birth": str(year_of_birth)
            },
            cards=deck_data,
            output_filename=output_filename
        )

        author = ctx.author.mention
        tournament_name = ""
        if tournament_id and tournament_id in self.tournaments:
            tournament_name = f"\n- Tournament: {self.tournaments[tournament_id].get('name', tournament_id)}"

        await channel.send(
            (
                f"New tournament signup:\n- Format: {format}\n"
                f"- Name: {full_name} ({author})\n"
                f"- Pokémon ID: {pokemon_id}\n"
                f"- Year of Birth: {year_of_birth}\n"
                f"- Decklist: {limitless_url}{tournament_name}"
            ),
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        self.record_tournament_signup(
            ctx.guild.id,
            ctx.author.id,
            full_name,
            pokemon_id,
            year_of_birth,
            limitless_url,
            format,
            tournament_id
        )

        await ctx.respond(
            "Tournament signup has been processed!",
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
        tournament_id: Optional[str] = None,
    ):
        await ctx.defer(ephemeral=True)
        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        # Check if tournament_id is provided, otherwise get open tournaments
        open_tournaments = self.get_open_tournaments()
        if not open_tournaments:
            await ctx.respond(
                "No tournaments are open at this moment.",
                ephemeral=True
            )
            return

        # If multiple tournaments are open and none specified, show dropdown
        if tournament_id is None:
            selected_tournament_id = await self.get_tournament_selection(
                ctx, open_tournaments
            )
            if selected_tournament_id is None:
                await ctx.respond(
                    "No tournament selected.",
                    ephemeral=True
                )
                return
            tournament_id = selected_tournament_id

        if tournament_id not in open_tournaments:
            await ctx.respond(
                "Selected tournament is not open.",
                ephemeral=True
            )
            return

        # Get format from tournament data
        tournament_data = self.tournaments.get(tournament_id, {})
        format = tournament_data.get("format", "standard")

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
            log_text = (
                f"Decklist for {full_name} failed validation: "
                f"{result[format]['error']}"
            )
            self.logger.info(log_text)
            await ctx.respond(
                f"Deck is not valid: {result[format]['error']}",
                ephemeral=True
            )
            return

        await self.tournament_signup_response(
            ctx, channel, deck_data, full_name, pokemon_id,
            year_of_birth, limitless_url, format, tournament_id
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

    def do_update_sheet(self) -> Exception:
        t = CustomThread(get_sign_up_sheet, kwargs={
            "output_filename": SIGN_UP_SHEET_FILE
        })
        t.start()
        _, error = t.join()
        return error

    def check_sign_up_sheet(self) -> bool:
        return os.path.exists(SIGN_UP_SHEET_FILE)
