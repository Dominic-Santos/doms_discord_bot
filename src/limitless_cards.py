import html
import json
import re
import time
import urllib.request
from urllib.parse import quote_plus

from .core import REPLACE_CHARACTERS

BASE_URL = "https://limitlesstcg.com"
SETS_URL = f"{BASE_URL}/cards"
SET_URL = f"{BASE_URL}/cards/{{set_code}}?display=list&show=all&page={{page}}"
SEARCH_URL = (
    f"{BASE_URL}/cards?q={{query}}&display=list&show=all&page={{page}}"
)
USER_AGENT = "Mozilla/5.0"
REQUEST_TIMEOUT = 60
REQUEST_DELAY = 0.5

SET_ROW = re.compile(
    r'<td><a href="/cards/([^"/]+)"><img class="set"[^>]*> '
    r'(.*?) <span class="code annotation">'
)
CARD_ROW = re.compile(r"<tr[^>]*data-hover.*?</tr>", re.DOTALL)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
TAGS = re.compile(r"<[^>]+>")
SYMBOL = re.compile(r'<span class="ptcg-symbol"[^>]*>([^<]*)</span>')
LINK = re.compile(r'href="([^"]+)"')
TOTAL = re.compile(r"([\d,]+) cards? found")
LAST_PAGE = re.compile(r'data-max="(\d+)"')

# the type of a Pokémon is shown as a symbol on the site
POKEMON_TYPE_SYMBOLS = {
    "C": "Colorless", "D": "Darkness", "N": "Dragon", "Y": "Fairy",
    "F": "Fighting", "R": "Fire", "G": "Grass", "L": "Lightning",
    "M": "Metal", "P": "Psychic", "W": "Water",
}


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read().decode("utf-8")


def clean_text(text: str) -> str:
    return html.unescape(TAGS.sub("", text)).strip()


def convert_card_type(type_cell: str) -> tuple[str, str]:
    # normalised to "Pkmn > Basic", "Trainer > Item" and "Energy > Basic"
    symbol = SYMBOL.search(type_cell)
    text = clean_text(SYMBOL.sub("", type_cell))
    if symbol is not None:
        color = POKEMON_TYPE_SYMBOLS.get(symbol.group(1).strip(), "")
        return f"Pkmn > {text}", color
    if text.endswith("Energy"):
        return f"Energy > {text.replace('Energy', '').strip()}", ""
    return f"Trainer > {text}", ""


def parse_card_rows(page: str) -> list[dict]:
    cards = []
    for row in CARD_ROW.findall(page):
        cells = CELL.findall(row)
        card_type, color = convert_card_type(cells[3])
        name = clean_text(cells[2])
        for old, new in REPLACE_CHARACTERS.items():
            name = name.replace(old, new)
        cards.append({
            "set": clean_text(cells[0]),
            "number": clean_text(cells[1]),
            "name": name,
            "type": card_type,
            "color": color,
            "rarity": clean_text(cells[4]),
            "link": BASE_URL + LINK.search(cells[1]).group(1),
        })
    return cards


def get_total_cards(page: str) -> int:
    total = TOTAL.search(page)
    return int(total.group(1).replace(",", "")) if total else 0


def get_all_pages(url: str) -> tuple[list[dict], str]:
    first_page = fetch_html(url.format(page=1))
    cards = parse_card_rows(first_page)
    last_page = LAST_PAGE.search(first_page)
    for page_number in range(2, int(last_page.group(1)) + 1 if last_page else 1):
        time.sleep(REQUEST_DELAY)
        cards += parse_card_rows(fetch_html(url.format(page=page_number)))
    return cards, first_page


def group_cards(cards: list[dict]) -> dict:
    grouped = {}
    for card in cards:
        grouped.setdefault(card["set"], {})[card["number"]] = {
            key: value for key, value in card.items()
            if key not in ("set", "number")
        }
    return grouped


def get_set_list() -> dict[str, str]:
    sets_page = fetch_html(SETS_URL)
    return {
        code: clean_text(name) for code, name in SET_ROW.findall(sets_page)
    }


def get_legal_card_list(
    current_format: str, previous_count: int
) -> tuple[dict, int]:
    # returns no cards when the total is unchanged since the last update
    url = SEARCH_URL.replace("{query}", quote_plus(f"f:{current_format}"))
    first_page = fetch_html(url.format(page=1))
    total = get_total_cards(first_page)
    if total == 0 or total == previous_count:
        return {}, total

    cards, _ = get_all_pages(url)
    ace_spec_url = SEARCH_URL.replace(
        "{query}", quote_plus(f"f:{current_format} is:ace-spec")
    )
    ace_specs = {
        (card["set"], card["number"])
        for card in get_all_pages(ace_spec_url)[0]
    }
    for card in cards:
        if (card["set"], card["number"]) in ace_specs:
            card["ace_spec"] = True
    return group_cards(cards), total


def get_legal_cards(
    filename: str = "legal_cards.json",
    expanded_filename: str = "legal_expanded_cards.json",
    standard_count: int = 0,
    expanded_count: int = 0
):
    formats = (
        ("standard", filename, standard_count),
        ("expanded", expanded_filename, expanded_count),
    )
    for current_format, file, previous_count in formats:
        legal_cards, total = get_legal_card_list(
            current_format, previous_count
        )
        if len(legal_cards) > 0:
            with open(file, "w") as f:
                json.dump({"cards": legal_cards, "count": total}, f, indent=4)


def get_pokemon_sets(filename: str = "card_sets.json"):
    pokemon_sets = {"black star promo": "SMP"}
    for code, name in get_set_list().items():
        pokemon_sets[name.lower()] = code

    with open(filename, "w") as f:
        json.dump(pokemon_sets, f, indent=4)


def get_all_cards(filename: str = "card_database.json"):
    try:
        with open(filename, "r") as f:
            all_cards = json.load(f).get("cards", {})
    except Exception:
        all_cards = {}

    for code in get_set_list():
        time.sleep(REQUEST_DELAY)
        cards, _ = get_all_pages(SET_URL.replace("{set_code}", code))
        all_cards[code] = group_cards(cards).get(code, {})
        # saved per set so an interrupted run keeps its progress
        with open(filename, "w") as f:
            json.dump({"cards": all_cards}, f, indent=4)
