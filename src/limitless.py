import re
from typing import Optional

URL_PREFIX = re.compile(r"^\s*(?:https?://)?", re.IGNORECASE)
BUILDER_MARKER = "builder?i="
QUANTITY_CHARS = (
    "123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
INVALID_DATA_ERROR = "Invalid decklist data in Limitless URL."
# separator + quantity + 2 discarded digits
CARD_PREFIX_LENGTH = 4


def parse_card_entries(
    data: str, set_codes: Optional[set[str]]
) -> Optional[list[tuple[int, str, str]]]:
    """Split the card entries from the end of the data backwards.

    Numbers can end in 0 and set codes can end in digits, so the split between
    set code and number is ambiguous. Known set codes resolve it, when
    set_codes is None any 2-5 character code with a letter is accepted.
    """
    results = {0: []}

    def parse(end: int) -> Optional[list[tuple[int, str, str]]]:
        if end in results:
            return results[end]
        results[end] = None
        for number_length in (3, 2, 1):
            for code_length in (2, 3, 4, 5):
                start = end - CARD_PREFIX_LENGTH - code_length - number_length
                if start < 0:
                    continue
                entry = data[start:end]
                code_end = CARD_PREFIX_LENGTH + code_length
                code = entry[CARD_PREFIX_LENGTH:code_end].upper()
                number = entry[code_end:]
                valid = (
                    entry[0] == "0"
                    and entry[1] in QUANTITY_CHARS
                    and entry[2:CARD_PREFIX_LENGTH].isdigit()
                    and code.isalnum()
                    and number.isdigit()
                    and number[0] != "0"
                )
                if set_codes is None:
                    valid = valid and not code.isdigit()
                else:
                    valid = valid and code in set_codes
                if not valid:
                    continue
                previous = parse(start)
                if previous is not None:
                    results[end] = previous + [(
                        QUANTITY_CHARS.index(entry[1]) + 1, code, number
                    )]
                    return results[end]
        return None

    return parse(len(data))


def parse_decklist_url(
    link: str, set_codes: Optional[set[str]] = None
) -> list[tuple[int, str, str]]:
    clean = URL_PREFIX.sub("", link.strip())
    if BUILDER_MARKER not in clean:
        raise ValueError("Invalid Limitless URL.")
    data = clean.split(BUILDER_MARKER, 1)[1].split("&")[0].split("#")[0]

    # first character is the version, every card starts with a 0 separator
    if not data.startswith("10"):
        raise ValueError(INVALID_DATA_ERROR)
    data = data[1:]

    known = {code.upper() for code in set_codes} if set_codes else None
    cards = parse_card_entries(data, known)
    # unknown set codes can't be matched, parse anyway to report the card
    if cards is None and known is not None:
        cards = parse_card_entries(data, None)
    if cards is None:
        raise ValueError(INVALID_DATA_ERROR)
    return cards


def build_card_lookup(card_database: dict) -> dict:
    lookup = {}
    for set_code, cards in (card_database or {}).get("cards", {}).items():
        for number, info in cards.items():
            key = (set_code.upper(), number.strip().lstrip("0") or "0")
            lookup.setdefault(key, {
                **info, "set": set_code
            })
    return lookup


def get_decklist_from_url(link: str, card_lookup: dict) -> dict:
    pokemon = []
    trainers = {}
    energies = {}

    set_codes = {set_code for set_code, _ in card_lookup}
    for quantity, set_code, number in parse_decklist_url(link, set_codes):
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
                "letter": info.get("regulation_mark", ""),
            })
        elif card_type.startswith("Trainer"):
            trainers.setdefault(name, {"quantity": 0})["quantity"] += quantity
        elif card_type.startswith("Energy"):
            energies.setdefault(name, {"quantity": 0})["quantity"] += quantity
        else:
            raise ValueError(f"Card {set_code} {number} has unknown type.")

    return {"pokemon": pokemon, "trainers": trainers, "energies": energies}
