import json

from .core import load_card_database, convert_banned_cards, DATA_FOLDER
from .pkmncards import get_legal_cards, get_pokemon_sets
from .pokemon import get_banned_cards

from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE

LEGAL_CARDS_FILE = f"{DATA_FOLDER}/legal_cards.json"
LEGAL_CARDS_EXPANDED_FILE = f"{DATA_FOLDER}/legal_expanded_cards.json"
BANNED_CARDS_FILE = f"{DATA_FOLDER}/banned_cards.json"
SETS_FILE = f"{DATA_FOLDER}/card_sets.json"


class LegalCardsBot:
    def load_legal_cards(self):
        try:
            pokemon, trainers, energies, count = load_card_database(
                LEGAL_CARDS_FILE,
                self.banned_sets
            )
            self.legal_cards = {
                "pokemon": pokemon,
                "trainers": trainers,
                "energies": energies,
                "count": count
            }
        except Exception as e:
            self.logger.warning(f"Error loading legal cards database: {e}")
            self.legal_cards = None

        try:
            pokemon, trainers, energies, count = load_card_database(
                LEGAL_CARDS_EXPANDED_FILE,
                self.banned_sets
            )
            self.legal_expanded_cards = {
                "pokemon": pokemon,
                "trainers": trainers,
                "energies": energies,
                "count": count
            }
        except Exception as e:
            self.logger.warning(
                f"Error loading legal expanded cards database: {e}"
            )
            self.legal_expanded_cards = None

        try:
            with open(LEGAL_CARDS_FILE, "r") as f:
                self.raw_standard_cards = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {LEGAL_CARDS_FILE}: {e}")
            self.raw_standard_cards = {}

        try:
            with open(LEGAL_CARDS_EXPANDED_FILE, "r") as f:
                self.raw_expanded_cards = json.load(f)
        except Exception as e:
            self.logger.warning(
                f"Error loading {LEGAL_CARDS_EXPANDED_FILE}: {e}"
            )
            self.raw_expanded_cards = {}

    def load_banned_cards(self):
        try:
            with open(BANNED_CARDS_FILE, "r") as f:
                self.banned_cards = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {BANNED_CARDS_FILE}: {e}")
            self.banned_cards = {"standard": None, "expanded": None}

    def save_banned_cards(self):
        try:
            with open(BANNED_CARDS_FILE, "w") as f:
                json.dump(self.banned_cards, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving {BANNED_CARDS_FILE}: {e}")

    def load_card_sets(self):
        try:
            with open(SETS_FILE, "r") as f:
                self.card_sets = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {SETS_FILE}: {e}")
            self.card_sets = {}

    def add_legal_cards_commands(self):
        @self.admin_pokemon.command(
            description="Sync the legal cards list for deck validation"
        )
        async def update_legal_cards(ctx):
            await self.get_legal_cards(ctx)  # pragma: no cover

        @self.admin_pokemon.command(
            description="Sync the banned cards list for deck validation"
        )
        async def update_banned_cards(ctx):
            await self.get_banned_cards(ctx)  # pragma: no cover

    def get_legal_cards_task(self):
        self.logger.info("Updating legal cards...")
        if self.maintenance:
            self.logger.info(
                "Won't update legal cards, Maintenance mode is active"
            )
            return

        error = self.do_get_legal_cards()
        if error is not None:
            self.logger.error(f"Legal cards update failed. {error}")
            return

        error = self.do_get_pokemon_sets()
        if error is not None:
            self.logger.error(f"Pokemon sets update failed. {error}")
            return
        self.logger.info("Legal cards updated successfully.")

    def get_banned_cards_task(self):
        self.logger.info("Updating banned cards...")
        if self.maintenance:
            self.logger.info(
                "Won't update banned cards, Maintenance mode is active"
            )
            return

        error = self.do_get_banned_cards()
        if error is not None:
            self.logger.error(f"Banned cards update failed. {error}")
            return
        self.logger.info("Banned cards updated successfully.")

    async def get_legal_cards(self, ctx):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        error = self.do_get_legal_cards()
        if error is not None:
            await ctx.respond(
                f"Legal cards update failed! {error}",
                ephemeral=True
            )
            return

        error = self.do_get_pokemon_sets()
        if error is not None:
            await ctx.respond(
                f"Pokemon sets update failed! {error}",
                ephemeral=True
            )
            return

        await ctx.respond("Legal cards list has been updated!", ephemeral=True)

    async def get_banned_cards(self, ctx):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        error = self.do_get_banned_cards()
        if error is not None:
            await ctx.respond(
                f"Banned cards update failed! {error}",
                ephemeral=True
            )
            return

        await ctx.respond(
            "Banned cards list has been updated!", ephemeral=True)

    def do_get_legal_cards(self) -> Exception | None:
        standard_count = 0
        expanded_count = 0
        if self.legal_cards is not None:
            standard_count = self.legal_cards.get("count", 0)
        if self.legal_expanded_cards is not None:
            expanded_count = self.legal_expanded_cards.get("count", 0)

        t = CustomThread(get_legal_cards, kwargs={
            "standard_count": standard_count,
            "expanded_count": expanded_count,
            "filename": LEGAL_CARDS_FILE,
            "expanded_filename": LEGAL_CARDS_EXPANDED_FILE,
        })
        t.start()
        _, error = t.join()
        self.load_legal_cards()
        return error

    def do_get_pokemon_sets(self) -> Exception | None:
        t = CustomThread(get_pokemon_sets, kwargs={
            "filename": SETS_FILE
        })
        t.start()
        _, error = t.join()
        self.load_card_sets()
        return error

    def do_get_banned_cards(self) -> Exception | None:
        t = CustomThread(get_banned_cards)
        t.start()
        banned_cards, error = t.join()

        if error is not None:
            return error

        self.banned_cards = convert_banned_cards(
            banned_cards,
            self.card_sets,
            self.raw_expanded_cards.get("cards", {})
        )
        self.save_banned_cards()
        return None
