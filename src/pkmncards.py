from datetime import datetime
from seleniumbase import Driver
import json

from .core import REPLACE_CHARACTERS

CARD_LIST_ULR = (
    "https://pkmncards.com/?s=format%3A{current_format}"
    "&sort=date&ord=auto&display=list"
)
SETS_URL = "https://pkmncards.com/sets/"


def get_legal_card_list(
        current_format: str, previous_count: int
) -> tuple[list[dict], bool, int]:
    legal_cards = []
    valid = True
    sb = Driver(uc=True, locale_code="en", ad_block=True)

    url = CARD_LIST_ULR.format(current_format=current_format)

    sb.uc_activate_cdp_mode(url)
    sb.sleep(2)

    headers = ["set", "number", "name", "type", "color", "rarity"]
    clean_total = 0

    while True:
        results = sb.cdp.find_visible_elements("li.results")[0].children[0]

        if results.text.lower().strip() == "no results":
            valid = False
            break

        current_range = sb.cdp.find_visible_elements("span.range-current")[0]
        total = sb.cdp.find_visible_elements("span.out-of")[0]

        range_max = current_range.text.replace(",", "").strip()
        if "thru" in range_max:
            range_max = range_max.split("thru")[1].strip()

        clean_total = total.children[0].text.replace(",", "")
        clean_total = clean_total.replace("/", "").strip()

        if int(clean_total) == previous_count:
            # Is up to date
            break

        card_elements = sb.cdp.find_visible_elements("article.type-pkmn_card")
        for card in card_elements:
            card_details = {}
            card_base = card.children[0].children[0].children
            for i, header in enumerate(headers):
                card_details[header] = card_base[i].text.strip()
            card_details["link"] = card_base[2].children[0]["href"]
            legal_cards.append(card_details)

        # check if last page
        if range_max == clean_total:
            break

        # trigger next page
        next_link_element = sb.cdp.find_visible_elements("li.next-link a")
        next_link_element[0].click()
        sb.sleep(3)

    sb.quit()
    return legal_cards, valid, int(clean_total)


def save_cards_to_file(
        cards: list[dict], count: int, filename: str = "legal_cards.json"
):
    final_cards = {}
    for card in cards:
        for k in card.keys():
            if k == "link":
                continue
            for old, new in REPLACE_CHARACTERS.items():
                card[k] = card[k].replace(old, new)

        final_cards.setdefault(card["set"], {})[card["number"]] = {
            "name": card["name"],
            "type": card["type"],
            "color": card["color"],
            "rarity": card["rarity"],
            "link": card["link"]
        }
    to_save = {
        "cards": final_cards,
        "count": count
    }
    json.dump(to_save, open(filename, "w"), indent=4)


def get_standard_format_from_date(date: datetime.date) -> str:
    format_year = date.year
    if date.month >= 4:
        format_year += 1
    format_letter = chr(ord("d") + (format_year - 2023))
    return f"{format_letter}-on-standard-{format_year}"


def get_extended_format() -> str:
    return "blw-on-expanded-current"


def get_legal_cards(
    filename: str = "legal_cards.json",
    expanded_filename: str = "legal_expanded_cards.json",
    standard_count: int = 0,
    expanded_count: int = 0
):
    current_date = datetime.now().date()
    previous_date = current_date.replace(month=1)

    standard_format = get_standard_format_from_date(current_date)
    legal_cards, valid, count = get_legal_card_list(
        standard_format, standard_count
    )

    # new format could be not ready yet
    if not valid and current_date.month == 4:
        standard_format = get_standard_format_from_date(previous_date)
        legal_cards, valid, count = get_legal_card_list(
            standard_format, standard_count
        )

    if len(legal_cards) > 0 and valid:
        save_cards_to_file(legal_cards, count, filename)

    expanded_format = get_extended_format()
    legal_cards, valid, count = get_legal_card_list(
        expanded_format, expanded_count
    )

    if len(legal_cards) > 0 and valid:
        save_cards_to_file(legal_cards, count, expanded_filename)


def get_card_text(card_link: str) -> str:
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(card_link)
    sb.sleep(1)
    query = "div.card-text-area div.card-tabs div.tab div.text"
    card_text = sb.cdp.find_visible_elements(query)[0].text.strip()
    sb.quit()
    return card_text.strip()


def get_pokemon_sets(
    filename: str = "card_sets.json",
):
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(SETS_URL)
    sb.sleep(1)
    query = "div.entry-content li a"
    set_elements = sb.cdp.find_visible_elements(query)

    pokemon_sets = {"black star promo": "SMP"}

    for element in set_elements:
        element_text = element.text.strip()
        if "(" not in element_text:
            continue
        set_name = element_text.split("(")[0].strip().lower()
        set_code = element_text.split("(")[1].replace(")", "").strip()
        pokemon_sets[set_name] = set_code

    sb.quit()
    json.dump(pokemon_sets, open(filename, "w"), indent=4)
