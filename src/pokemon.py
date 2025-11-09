import fitz  # PyMuPDF
import os
from seleniumbase import Driver
from datetime import datetime, timedelta
import shutil
from urllib.request import urlretrieve
import requests
from .core import DATA_FOLDER, REPLACE_CHARACTERS

POKEMON_EVENTS_BASE_URL = "https://events.pokemon.com"
POKEMON_RULES_URL = (
    "https://www.pokemon.com/us/play-pokemon/"
    "about/tournaments-rules-and-resources"
)
POKEMON_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/LocationDetail"
POKEMON_PREMIER_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/Home"
POKEMON_BANNED_CARDS_URL = (
    "https://www.pokemon.com/us/play-pokemon/"
    "about/pokemon-tcg-banned-card-list"
)
EVENT_DATE_FORMAT = "%b %d %Y"
TMP_FILE = f"{DATA_FOLDER}/tmp.pdf"


class PokemonEvent():
    def __init__(
        self,
        name: str,
        type: str,
        location: str,
        date: str,
        logo: str,
        premier: bool
    ):
        self.name = name
        self.type = type
        self.location = location
        self.logo = logo
        self.premier = premier

        self._parse_date(date)

    def _parse_date(self, date: str):
        e_date = date.replace(", ", ",").replace(",", " ")

        if "-" in e_date:
            # Friday Oct 10 - Sunday 12 2025
            d_split = e_date.split(" ")
            start_month, start_day = d_split[1:3]
            year = d_split[-1]
            if len(d_split) == 7:
                end_month = start_month
                end_day = d_split[5]
            else:
                end_month, end_day = d_split[5:7]

            start_str = f"{start_month[:3]} {start_day} {year}"
            end_str = f"{end_month[:3]} {end_day} {year}"

            self.start_date = datetime.strptime(
                start_str, EVENT_DATE_FORMAT
            )
            self.end_date = datetime.strptime(
                end_str, EVENT_DATE_FORMAT
            ) + timedelta(days=1)
            return

        # Wednesday September 24 2025 03:00 PM
        month, day, year = e_date.split(" ")[1:4]
        e_date = f"{month[:3]} {day} {year}"

        event_date = datetime.strptime(
            e_date,
            EVENT_DATE_FORMAT
        )
        self.start_date = event_date
        self.end_date = event_date + timedelta(days=1)


def convert_pdf_to_png(in_file: str, out_file: str):
    doc = fitz.open(in_file)  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.0, 2.0)
        )  # render page to an image
        pix.save(out_file)


def get_decklist_pdf(output_filename: str):
    sb = Driver(uc=True, locale_code="en", ad_block=True, external_pdf=True)
    sb.uc_activate_cdp_mode(POKEMON_RULES_URL)
    sb.sleep(10)
    a_elements = sb.cdp.find_visible_elements("a")

    for a in a_elements:
        if (
            a.get_attribute("innerHTML").strip()
            == "Play! Pokémon Deck List (A4)"
        ):
            a.click()
            sb.sleep(5)
            break
    else:
        raise Exception("Couldn't find sheet in page")

    for file in os.listdir("downloaded_files"):
        if file.endswith(".pdf"):
            pdf_path = os.path.join("downloaded_files", file)
            if os.path.exists(pdf_path):
                if os.path.exists(output_filename):
                    os.remove(
                        output_filename
                    )  # Remove existing file if it exists
                os.rename(pdf_path, output_filename)
            break
    else:
        raise Exception("No pdf in downloaded files")

    sb.quit()
    # Clean up the directory
    shutil.rmtree("downloaded_files", ignore_errors=True)


def get_decklist_png(output_filename: str = "sign_up_sheet.png"):
    get_decklist_pdf(TMP_FILE)
    convert_pdf_to_png(TMP_FILE, output_filename)
    # Clean up temporary files if necessary
    os.remove(TMP_FILE)


def get_premier_events() -> list[PokemonEvent]:
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(POKEMON_PREMIER_EVENTS_URL)
    sb.sleep(10)

    tabs = sb.cdp.find_visible_elements("button.osui-tabs__header-item")

    if len(tabs) < 2:
        raise Exception("Failed to load events page")

    tabs[1].click()
    sb.sleep(2)

    # scroll to end of page to let more events load
    prev_event = None
    while True:
        events = sb.cdp.find_visible_elements("div.map-location-card")
        last_event = events[-1]
        event_info = extract_event_info(last_event)
        if prev_event is not None and event_info.name == prev_event.name:
            break
        prev_event = event_info
        last_event.scroll_into_view()
        sb.sleep(1)
        sb.cdp.scroll_up(amount=25)
        sb.sleep(1)
        sb.cdp.scroll_down(amount=25)
        sb.sleep(5)

    events = []

    event_divs = sb.cdp.find_visible_elements("div.map-location-card")
    for div in event_divs:
        event_info = extract_event_info(div)
        events.append(event_info)

    sb.quit()
    return events


def get_store_events(guids: list[str] = []) -> list[PokemonEvent]:
    if len(guids) == 0:
        return []

    events = {}
    sb = Driver(uc=True, locale_code="en", ad_block=True)

    for guid in guids:
        sb.uc_activate_cdp_mode(f"{POKEMON_EVENTS_URL}?guid={guid}")
        sb.sleep(10)

        events[guid] = []

        events_div = sb.cdp.find_visible_elements(
            "#b10-Content"
        )[0].children[0].children
        for event in events_div:
            div = event
            for _ in range(5):
                div = div.children[0]
            event_info = extract_event_info(div, store=True)
            events[guid].append(event_info)

    sb.quit()
    return events


def extract_event_info(div, store: bool = False) -> PokemonEvent:
    img = div.children[1].children[0].children[0].children[0]
    if store:
        img = img.children[0]

    logo = img["src"]
    base = div.children[0].children[0].children[0].children[0].children[0]
    event_type = base.children[0].children[0].text
    event_name = base.children[1].children[0].text
    event_loca = base.children[2].children[1].children[0].text
    event_date = base.children[3].children[1].children[0].text
    premier = not store
    return PokemonEvent(
        event_name,
        event_type,
        event_loca,
        event_date,
        logo,
        premier
    )


def get_logo(url: str) -> bytes:
    if ";base64," in url:
        filename, _ = urlretrieve(url)
        f = open(filename, "rb")
        return f.read()

    full_url = f"{POKEMON_EVENTS_BASE_URL}{url}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.content


def get_banned_cards() -> dict[str, list]:
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(POKEMON_BANNED_CARDS_URL)
    sb.sleep(10)

    card_elements = sb.cdp.find_visible_elements("ul.list")
    standard_elms = card_elements[0].children
    expanded_elms = card_elements[1].children

    standard_cards = []
    expanded_cards = []

    for cards, elms in (
        (standard_cards, standard_elms),
        (expanded_cards, expanded_elms)
    ):
        for li in elms:
            p = li.children[0]
            p_text = p.text.strip()
            if p_text.startswith("No cards are currently banned"):
                break

            card_name, card_sets = p_text.split("(")
            card_name = card_name.strip()
            for old, new in REPLACE_CHARACTERS.items():
                card_name = card_name.replace(old, new)
            card_sets = card_sets.replace(")", "").strip()

            all_sets = card_sets.split(";")

            for each_set in all_sets:
                set_text = each_set.replace("and", ",")
                for old, new in REPLACE_CHARACTERS.items():
                    set_text = set_text.replace(old, new)

                if "—" in set_text:
                    set_text = set_text.split("—")[1]
                parts = set_text.split(",")
                set_name = parts[0].strip()
                for part in parts[1:]:
                    set_nr = part.strip()
                    if set_nr == "":
                        continue
                    if "/" in set_nr:
                        set_nr = set_nr.split("/")[0].strip()
                    cards.append((card_name, set_name, set_nr))

    sb.quit()
    return {
        "standard": standard_cards,
        "expanded": expanded_cards
    }
