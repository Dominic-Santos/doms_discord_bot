import json
from datetime import date

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

DATA_FOLDER = "data"

ENERGY_TYPES = [
    "fire", "water", "grass", "lightning", "psychic",
    "fighting", "darkness", "metal"
]

REPLACE_CHARACTERS = {
    "’": "'",
    "›": ">",
}


SEASON_START_MONTH = 9
FORMAT_X = {"standard": 299, "expanded": 398}
FORMAT_Y = 105
AGE_DIVISION_Y = {"junior": 231, "senior": 258, "masters": 285}


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


def get_season_year(today: date = None) -> int:
    # a season is named after the year it ends in, and starts after the summer
    today = today or date.today()
    return today.year + 1 if today.month >= SEASON_START_MONTH else today.year


def get_age_division(year_of_birth: int, today: date = None) -> str:
    # the 2026 season has juniors born in 2014 or later and seniors born
    # 2010-2013, every following season moves these ranges up by one year
    shift = get_season_year(today) - 2026
    if year_of_birth >= 2014 + shift:
        return "junior"
    if year_of_birth >= 2010 + shift:
        return "senior"
    return "masters"


def fill_sheet(
    sheet_location: str = "sign_up_sheet.png",
    player: dict = {},
    cards: dict = {},
    output_filename: str = None,
    format: str = None
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

    draw.text(
        (1086, 140),
        str(player.get("year_of_birth", "1990")),
        (0, 0, 0),
        font=player_name_font
    )

    if format in FORMAT_X:
        draw.text(
            (FORMAT_X[format], FORMAT_Y),
            "X",
            (0, 0, 0),
            font=player_name_font,
            anchor="mm"
        )

    year_of_birth = player.get("year_of_birth")
    if year_of_birth is not None:
        draw.text(
            (742, AGE_DIVISION_Y[get_age_division(int(year_of_birth))]),
            "X",
            (0, 0, 0),
            font=player_name_font,
            anchor="mm"
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


def load_card_database(
    filename: str = "legal_cards.json",
    banned_sets: list[str] = []
) -> tuple[dict, dict, dict, int]:
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
        if set_name in banned_sets:
            continue
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
    legal_cards: dict = None,
    banned_cards: dict = None,
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
            if card.get("ace_spec")
        ]
        ace_spec_energies = [
            card_name.lower() for
            card_name, card in legal_cards["energies"].items()
            if card.get("ace_spec")
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
