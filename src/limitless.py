import re

from .core import remove_types_from_card_name

URL_PREFIX = re.compile(r"^\s*(?:https?://)?", re.IGNORECASE)
BUILDER_MARKER = "builder?i="
CARD_PATTERN = re.compile(
    r"0([1-9a-zA-Z])(\d{2})([A-Za-z]{2,3})(\d{1,3})$"
)
QUANTITY_CHARS = (
    "123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)


def parse_decklist_url(link: str) -> list[tuple[int, str, str]]:
    clean = URL_PREFIX.sub("", link.strip())
    if BUILDER_MARKER not in clean:
        raise ValueError("Invalid Limitless URL.")
    data = clean.split(BUILDER_MARKER, 1)[1].split("&")[0].split("#")[0]

    # first character is the version, every card starts with a 0 separator
    if not data.startswith("10"):
        raise ValueError("Invalid decklist data in Limitless URL.")
    data = data[1:]

    # numbers can end in 0, so the string has to be read from the end
    cards = []
    while data:
        match = CARD_PATTERN.search(data)
        if match is None or match.end() != len(data):
            raise ValueError("Invalid decklist data in Limitless URL.")
        quantity, _, set_code, number = match.groups()
        cards.append((
            QUANTITY_CHARS.index(quantity) + 1,
            set_code.upper(),
            number.lstrip("0") or "0",
        ))
        data = data[:match.start()]

    cards.reverse()
    return cards


def normalise_card_name(info: dict) -> str:
    name = remove_types_from_card_name(info["name"])
    card_type = info["type"]
    # newer sets say "Basic Grass Energy", older ones "Grass Energy"
    if card_type.startswith("Energy") and card_type.endswith("Basic"):
        name = re.sub(r"^Basic\s+", "", name)
    return name


def build_card_lookup(card_database: dict) -> dict:
    lookup = {}
    for set_code, cards in (card_database or {}).get("cards", {}).items():
        for number, info in cards.items():
            key = (set_code.upper(), number.strip().lstrip("0") or "0")
            lookup.setdefault(key, {
                **info, "name": normalise_card_name(info), "set": set_code
            })
    return lookup


def get_decklist_from_url(link: str, card_lookup: dict) -> dict:
    pokemon = []
    trainers = {}
    energies = {}

    for quantity, set_code, number in parse_decklist_url(link):
        info = card_lookup.get((set_code, number))
        if info is None:
            raise ValueError(f"Unknown card {set_code} {number}")

        name = info["name"]
        card_type = info["type"]
        if card_type.startswith("Pkmn"):
            pokemon.append({
                "quantity": quantity,
                "name": name,
                "set": info["set"],
                "number": int(number) if number.isdigit() else number,
            })
        elif card_type.startswith("Trainer"):
            trainers.setdefault(name, {"quantity": 0})["quantity"] += quantity
        elif card_type.startswith("Energy"):
            energies.setdefault(name, {"quantity": 0})["quantity"] += quantity
        else:
            raise ValueError(f"Card {set_code} {number} has unknown type.")

    return {"pokemon": pokemon, "trainers": trainers, "energies": energies}
