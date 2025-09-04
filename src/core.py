import json

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

ENERGY_TYPES = [
    "fire", "water", "grass", "lightning", "psychic",
    "fighting", "darkness", "metal"
]


def get_offset(card_type: str, amount: int) -> int:
    if card_type == "pokemon":
        if amount > 13:
            return 19
        elif amount > 11:
            return 23
    elif card_type == "trainer":
        if amount > 19:
            return 23
    return 27


def fill_sheet(
    sheet_location: str = "sign_up_sheet.png",
    player: dict = {},
    cards: dict = {},
    output_filename: str | None = None
):

    if not sheet_location.endswith(".png"):
        raise ValueError("Sheet location must be a PNG file.")

    if output_filename is None:
        player_name = player.get("name", None)
        if player_name is None:
            output_filename = sheet_location.replace(".png", "_out.png")
        else:
            output_filename = player_name.lower().replace(" ", "_") + ".png"

    img = Image.open(sheet_location)
    draw = ImageDraw.Draw(img)

    player_name_font = ImageFont.truetype("arial.ttf", 24)

    draw.text(
        (170, 140),
        player.get("name", "Player Name"),
        (0, 0, 0),
        font=player_name_font
    )
    draw.text(
        (550, 140),
        player.get("id", "123456789"),
        (0, 0, 0),
        font=player_name_font
    )

    quantity_x = 525
    card_name_x = 580
    set_x = 922
    set_nr_x = 1000
    set_letter_x = 1085

    pokemon = sorted(
        cards.get("pokemon", []), key=lambda x: x.get("name", "zzzzzzzzzzzzz")
    )
    offset = get_offset("pokemon", len(pokemon))

    for i, card in enumerate(pokemon):
        y = 372 + i * offset - (1 * i // 1.5)
        draw.text(
            (quantity_x, y),
            str(card.get("quantity", 0)),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text(
            (card_name_x, y),
            card.get("name", "card name"),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text(
            (set_x, y),
            card.get("set", "ABC"),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text(
            (set_nr_x, y),
            str(card.get("number", 0)),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text(
            (set_letter_x, y),
            card.get("letter", "ABC"),
            (0, 0, 0),
            font=player_name_font
        )

    trainers = cards.get("trainers", {})
    offset = get_offset("trainer", len(trainers))

    for i, card in enumerate(sorted(trainers.keys())):
        y = 725 + i * offset - (1 * i // 1.5)
        draw.text(
            (quantity_x, y),
            str(trainers[card].get("quantity", 0)),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text((card_name_x, y), card, (0, 0, 0), font=player_name_font)

    energies = cards.get("energies", {})
    offset = get_offset("energy", len(energies))

    for i, card in enumerate(sorted(energies.keys())):
        y = 1288 + i * offset - (1 * i // 1.5)
        draw.text(
            (quantity_x, y),
            str(energies[card].get("quantity", 0)),
            (0, 0, 0),
            font=player_name_font
        )
        draw.text((card_name_x, y), card, (0, 0, 0), font=player_name_font)

    img.save(output_filename)


def load_card_database(filename: str = "legal_cards.json") -> tuple[
    dict, dict, dict, int
]:
    if not filename.endswith(".json"):
        raise ValueError("Filename must be a JSON file.")
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except Exception:
        raise ValueError("Error loading JSON file.")

    pokemon = {}
    trainers = {}
    energies = {}
    count = data.get("count", 0)

    for set_name, cards in data.get("cards", {}).items():
        for card_number, card_info in cards.items():
            if card_info["type"].startswith("Pkmn"):
                if card_number.isdigit():
                    clean_number = str(int(card_number))
                else:
                    clean_number = card_number.strip()
                pokemon.setdefault(set_name, {})[
                    clean_number
                ] = card_info.copy()
            elif card_info["type"].startswith("Trainer"):
                trainers[card_info["name"]] = card_info.copy()
            elif (
                card_info["type"].startswith("Energy") and
                not card_info["type"].endswith("Basic")
            ):
                energies[card_info["name"]] = card_info.copy()

    return pokemon, trainers, energies, count


def validate_decklist(
    decklist: dict,
    legal_cards: dict | None = None,
    banned_cards: dict | None = None
) -> tuple[bool, str]:
    # check 60 card deck
    pokemon_count = sum(
        card["quantity"] for card in decklist.get("pokemon", [])
    )
    trainer_count = sum(
        card["quantity"] for card in decklist.get("trainers", {}).values()
    )
    energy_count = sum(
        card["quantity"] for card in decklist.get("energies", {}).values()
    )
    count = pokemon_count + trainer_count + energy_count
    if count != 60:
        return False, "Decklist must contain exactly 60 cards."

    # check if at least 1 pokemon
    if pokemon_count < 1:
        return False, "Decklist must contain at least 1 Pokémon."

    # check max 4 copies of each card
    quantities_by_name = {}
    for card in decklist.get("pokemon", []):
        quantities_by_name[card["name"].lower()] = quantities_by_name.get(
            card["name"].lower(), 0
        ) + card["quantity"]

    for card, data in decklist.get("trainers", {}).items():
        quantities_by_name[card.lower()] = quantities_by_name.get(
            card.lower(), 0
        ) + data["quantity"]

    for card, data in decklist.get("energies", {}).items():
        quantities_by_name[card.lower()] = quantities_by_name.get(
            card.lower(), 0
        ) + data["quantity"]

    exemptions = [f"{t} energy" for t in ENERGY_TYPES]
    for name, quantity in quantities_by_name.items():
        if quantity > 4 and name not in exemptions:
            return False, f"Card {name} exceeds the maximum of 4 copies."

    if legal_cards is not None:
        # ace spec cards can only be included once
        ace_spec_trainers = [
            card_name.lower() for
            card_name, card in legal_cards["trainers"].items()
            if card["rarity"] == "ACE SPEC Rare"
        ]
        ace_spec_energies = [
            card_name.lower() for
            card_name, card in legal_cards["energies"].items()
            if card["rarity"] == "ACE SPEC Rare"
        ]
        total_ace_specs = sum(
            quantities_by_name[card.lower()] for
            card in quantities_by_name.keys()
            if card.lower() in ace_spec_trainers
            or card.lower() in ace_spec_energies
        )
        if total_ace_specs > 1:
            return False, "Decklist can only contain one Ace Spec card."

        # check if all pokemon cards are legal and at least 1 basic pokemon
        basic_pokemon_found = False
        for card in decklist.get("pokemon", []):
            card_info = legal_cards["pokemon"].get(
                card["set"], {}
            ).get(str(card["number"]), None)
            if card_info is None:
                return False, (
                    f"Card {card['name']} from set {card['set']}"
                    " is not legal."
                )

            if (
                card_info["type"].startswith("Pkmn")
                and "Basic" in card_info["type"]
            ):
                basic_pokemon_found = True

        if not basic_pokemon_found:
            return False, "Decklist must contain at least one Basic Pokémon."

        # check if all trainer cards are legal
        for card_name, quantity in decklist.get("trainers", {}).items():
            if card_name not in legal_cards["trainers"]:
                return False, f"Trainer card {card_name} is not legal."

        # check if all energy cards are legal
        for card_name, quantity in decklist.get("energies", {}).items():
            if (
                card_name not in legal_cards["energies"]
                and card_name.lower() not in exemptions
            ):
                return False, f"Energy card {card_name} is not legal."

    if banned_cards is not None:
        # check if all pokemon cards are not banned
        for card in decklist.get("pokemon", []):
            banned_set = banned_cards["pokemon"].get(card["set"], [])
            if str(card["number"]) in banned_set:
                return False, (
                    f"Card {card['name']} from set {card['set']}"
                    " is banned."
                )

        # check if all trainer cards are not banned
        for card_name in decklist.get("trainers", {}):
            if card_name in banned_cards["trainers"]:
                return False, (
                    f"Trainer card {card_name} is banned."
                )

        # check if all energy cards are not banned
        for card_name in decklist.get("energies", {}):
            if (
                card_name in banned_cards["energies"]
                and card_name.lower() not in exemptions
            ):
                return False, f"Energy card {card_name} is banned."

    return True, ""


def convert_banned_cards(banned_cards: dict, sets: dict, expanded_cards: dict):
    new_banned_cards = {}
    for format in banned_cards.keys():
        new_banned_cards[format] = {
            "pokemon": {}, "trainers": [], "energies": []
        }
        for card_name, set_name, set_nr in banned_cards[format]:
            set_code = sets.get(set_name.lower(), set_name)
            if set_code not in expanded_cards:
                raise Exception(
                    f"Set code {set_code} not found in expanded cards."
                )

            if set_nr not in expanded_cards[set_code]:
                raise Exception(
                    f"Card number {set_code}-{set_nr} "
                    "not found in expanded cards."
                )

            card_info = expanded_cards[set_code][set_nr]
            if card_info["type"].startswith("Pkmn"):
                category = "pokemon"
            elif card_info["type"].startswith("Trainer"):
                category = "trainers"
            elif card_info["type"].startswith("Energy"):
                category = "energies"
            else:
                raise Exception(
                    f"Card {set_code}-{set_nr}"
                    f" has unknown type {card_info['type']}."
                )

            if category == "pokemon":
                if set_code not in new_banned_cards[format]["pokemon"]:
                    new_banned_cards[format]["pokemon"][set_code] = []

                new_banned_cards[format][category][set_code].append(set_nr)
            else:
                if card_name not in new_banned_cards[format][category]:
                    new_banned_cards[format][category].append(card_name)

    return new_banned_cards
