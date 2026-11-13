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
# numbers may have a letter prefix, e.g. Trainer Gallery TG24
CARD_NUMBER = re.compile(r"^(?:[1-9][0-9]{0,2}|[A-Za-z]{1,3}[1-9][0-9]{0,2})$")


def parse_card_entries(
    data: str,
    set_codes: Optional[set[str]],
    cards: Optional[set[tuple[str, str]]] = None,
) -> Optional[list[tuple[int, str, str]]]:
    """Split the card entries from the end of the data backwards.

    Numbers can end in 0 and set codes can end in digits, so the split between
    set code and number is ambiguous. Known set codes resolve it, when
    set_codes is None any 2-5 character code with a letter is accepted and
    numbers must be plain digits (letter prefixes like TG24 are ambiguous).
    When cards ((set code, number) pairs) is given a split must be a real
    card, which separates sets like DR and DRI that share a prefix.
    """
    results = {0: []}

    def parse(end: int) -> Optional[list[tuple[int, str, str]]]:
        if end in results:
            return results[end]
        results[end] = None
        for number_length in (3, 2, 1, 4, 5, 6):
            for code_length in (2, 3, 4, 5):
                start = end - CARD_PREFIX_LENGTH - code_length - number_length
                if start < 0:
                    continue
                entry = data[start:end]
                code_end = CARD_PREFIX_LENGTH + code_length
                code = entry[CARD_PREFIX_LENGTH:code_end].upper()
                number = entry[code_end:].upper()
                valid = (
                    entry[0] == "0"
                    and entry[1] in QUANTITY_CHARS
                    and entry[2:CARD_PREFIX_LENGTH].isdigit()
                    and code.isalnum()
                    and CARD_NUMBER.match(number) is not None
                    and (set_codes is not None or number.isdigit())
                )
                if set_codes is None:
                    valid = valid and not code.isdigit()
                else:
                    valid = valid and code in set_codes
                if cards is not None:
                    valid = valid and (code, number) in cards
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
    link: str,
    set_codes: Optional[set[str]] = None,
    cards: Optional[set[tuple[str, str]]] = None,
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
    parsed = parse_card_entries(data, known, cards)
    # unknown cards can't be matched, parse anyway to report the card
    if parsed is None and known is not None:
        parsed = parse_card_entries(data, None)
    if parsed is None:
        raise ValueError(INVALID_DATA_ERROR)
    return parsed


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

    known_cards = {(set_code, number.upper()) for set_code, number in card_lookup}
    set_codes = {set_code for set_code, _ in known_cards}
    for quantity, set_code, number in parse_decklist_url(
        link, set_codes, known_cards
    ):
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
