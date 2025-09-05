import json
import discord
from datetime import datetime

from .limitless import get_decklist_from_url
from .core import validate_decklist, DATA_FOLDER
from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE

USER_DECKLIST_FILE = f"{DATA_FOLDER}/user_decklists.json"


class DecklistBot:
    def load_user_decklists(self):
        try:
            with open(USER_DECKLIST_FILE, "r") as f:
                self.user_decklists = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {USER_DECKLIST_FILE}: {e}")
            self.user_decklists = {}

    def save_user_decklists(self):
        try:
            with open(USER_DECKLIST_FILE, "w") as f:
                json.dump(self.user_decklists, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving {USER_DECKLIST_FILE}: {e}")

    def add_decklist_commands(self):
        decklist = self.bot.create_group(
            "deck", "Manage your decks"
        )
        pokemon_decklist = decklist.create_subgroup(
            "pokemon", "Manage Pokémon decklists"
        )

        @pokemon_decklist.command(
            description="Check a limitless decklist is legal"
        )
        async def check_url(
            ctx,
            limitless_url: discord.Option(
                str, "Limitless URL of the decklist"
            ),  # type: ignore
        ):
            await self.decklist_check_url(
                ctx, limitless_url
            )  # pragma: no cover

        @pokemon_decklist.command(
            description="Check a saved deck is legal"
        )
        async def check(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_check(ctx, name)  # pragma: no cover

        @pokemon_decklist.command(description="Create a deck")
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

        @pokemon_decklist.command(description="Delete a saved deck")
        async def delete(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_delete(ctx, name)  # pragma: no cover

        @pokemon_decklist.command(name="list", description="List saved decks")
        async def list_all(ctx):
            await self.decklist_list(ctx)  # pragma: no cover

        @pokemon_decklist.command(description="Show deck info")
        async def info(
            ctx,
            name: discord.Option(
                str, "Deck name"
            ),  # type: ignore
        ):
            await self.decklist_info(ctx, name)  # pragma: no cover

    async def decklist_info(self, ctx, name: str):
        user_id = str(ctx.author.id)
        name = name.strip()

        deck_data = self.user_decklists.get(user_id, {}).get(name, None)
        if deck_data is None:
            await ctx.respond("Deck not found", ephemeral=True)
            return

        deck_info = f"{name}\nStandard Legal: "
        if deck_data["standard"]["valid"]:
            deck_info += ":white_check_mark:"
        else:
            deck_info += f":x: - {deck_data['standard']['error']}"

        deck_info += "\nExpanded Legal: "
        if deck_data["expanded"]["valid"]:
            deck_info += ":white_check_mark:"
        else:
            deck_info += f":x: - {deck_data['expanded']['error']}"

        deck_info += f"\nLast Checked: {deck_data['last_checked']}"

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
                    f"\t{trainers[t]['quantity']}x {t}"
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
                    f"\t{energies[t]['quantity']}x {t}"
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

        result, error = self.do_user_decklist_check(user_id, name)

        if error is not None:
            await ctx.respond(f"Error checking deck: {error}", ephemeral=True)
            return

        result_text = "Deck is:\n- standard "
        if result["standard"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['standard']['error']}"

        result_text += "\n- expanded "
        if result["expanded"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['expanded']['error']}"

        await ctx.respond(result_text, ephemeral=True)

    async def decklist_create(self, ctx, name: str, limitless_url: str):
        await ctx.defer(ephemeral=True)
        user_id = str(ctx.author.id)
        name = name.strip()
        if user_id not in self.user_decklists:
            self.user_decklists[user_id] = {}

        self.user_decklists[user_id][name] = {
            "url": limitless_url
        }

        result, error = self.do_user_decklist_check(user_id, name)

        if error is not None:
            await ctx.respond(
                f"Deck saved, error checking deck: {error}",
                ephemeral=True
            )
            return

        result_text = "Deck saved, deck is:\n- standard "
        if result["standard"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['standard']['error']}"

        result_text += "\n- expanded "
        if result["expanded"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['expanded']['error']}"

        await ctx.respond(result_text, ephemeral=True)
        self.save_user_decklists()

    async def decklist_check_url(self, ctx, deck_url: str):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        result, _, error = self.do_decklist_check(deck_url)
        if error is not None:
            await ctx.respond(
                f"Error checking deck: {error}",
                ephemeral=True
            )
            return

        result_text = "Deck check complete:\n- standard "
        if result["standard"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['standard']['error']}"

        result_text += "\n- expanded "
        if result["expanded"]["valid"]:
            result_text += "valid!"
        else:
            result_text += f"not valid! {result['expanded']['error']}"
        await ctx.respond(result_text, ephemeral=True)

    def do_user_decklist_check(
        self, user_id: str, deck_name: str
    ) -> tuple[dict, str]:
        deck_data = self.user_decklists.get(
            user_id, {}
        ).get(deck_name, None)

        if deck_data is None:
            return None, "Deck not found"

        decklist_url = deck_data["url"]

        valid, deck_data, error = self.do_decklist_check(decklist_url)
        self.user_decklists[user_id][deck_name].update(
            {
                "deck": deck_data,
                "last_checked": str(datetime.now().date())
            }
        )
        if error is not None:
            self.user_decklists[user_id][deck_name].update(
                {
                    "standard": {
                        "valid": False,
                        "error": error
                    },
                    "expanded": {
                        "valid": False,
                        "error": error
                    }
                }
            )
        else:
            self.user_decklists[user_id][deck_name].update(valid)

        self.save_user_decklists()
        return valid, error

    def do_decklist_check(self, limitless_url: str) -> tuple[dict, dict, str]:
        valid = self.check_limitless_url(limitless_url)
        if not valid:
            return {}, {}, "Invalid Limitless URL."
        t = CustomThread(get_decklist_from_url, args=(limitless_url,))
        t.start()
        deck_data, error = t.join()

        if error is not None:
            return {}, {}, str(error)

        valid = self.validate_decklist_all_formats(deck_data)
        return valid, deck_data, None

    def validate_decklist_all_formats(self, deck_data):
        standard_valid, standard_error = validate_decklist(
            deck_data, self.legal_cards, self.banned_cards["standard"])
        expanded_valid, expanded_error = validate_decklist(
            deck_data, self.legal_expanded_cards,
            self.banned_cards["expanded"])
        result = {
            "standard": {
                "valid": standard_valid,
                "error": standard_error
            },
            "expanded": {
                "valid": expanded_valid,
                "error": expanded_error
            }
        }
        return result

    def check_limitless_url(self, url: str) -> tuple[bool]:
        clean = url.strip("https://").strip("http://")
        if clean.startswith("my.limitlesstcg.com/builder?i="):
            return True
        return False
