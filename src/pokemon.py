import fitz  # PyMuPDF
import os
from seleniumbase import Driver
from datetime import datetime, timedelta
import shutil

POKEMON_EVENTS_BASE_URL = "https://events.pokemon.com"
POKEMON_RULES_URL = (
    "https://www.pokemon.com/us/play-pokemon/"
    "about/tournaments-rules-and-resources"
)
POKEMON_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/LocationDetail"
POKEMON_PREMIER_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/Home"
EVENT_DATE_FORMAT = "%b %d,%Y"


class Pokemon_Event():
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
        e_date = date.replace(", ", ",")
        e_date = e_date[:3] + " " + e_date.split(" ")[1]

        if "-" in e_date:
            start_str = e_date[:6] + e_date[9:]
            end_str = e_date[0:4] + e_date[7:]
            self.start_date = datetime.strptime(
                start_str, EVENT_DATE_FORMAT
            )
            self.end_date = datetime.strptime(
                end_str, EVENT_DATE_FORMAT
            ) + timedelta(days=1)
            return

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
    sb.sleep(5)
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
    shutil.rmtree('downloaded_files', ignore_errors=True)


def get_decklist_png(output_filename: str = "sign_up_sheet.png"):
    get_decklist_pdf("tmp.pdf")
    convert_pdf_to_png("tmp.pdf", output_filename)
    # Clean up temporary files if necessary
    os.remove("tmp.pdf")


def get_premier_events() -> list[Pokemon_Event]:
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(POKEMON_PREMIER_EVENTS_URL)
    sb.sleep(5)
    tabs = sb.cdp.find_visible_elements("button.osui-tabs__header-item")

    if len(tabs) < 2:
        raise Exception("Failed to load events page")

    tabs[1].click()
    sb.sleep(2)

    events = []

    event_divs = sb.cdp.find_visible_elements("div.map-location-card")
    for div in event_divs:
        event_info = extract_event_info(div)
        events.append(event_info)

    sb.quit()
    return events


def get_store_events(guids: list[str] = []) -> list[Pokemon_Event]:
    if len(guids) == 0:
        return []

    events = {}
    sb = Driver(uc=True, locale_code="en", ad_block=True)

    for guid in guids:
        sb.uc_activate_cdp_mode(f"{POKEMON_EVENTS_URL}?guid={guid}")
        sb.sleep(5)

        events[guid] = []

        events_div = sb.cdp.find_visible_elements(
            '#b10-Content'
        )[0].children[0].children
        for event in events_div:
            div = event.children[0].children[0].children[0].children[0]
            event_info = extract_event_info(div, store=True)
            events[guid].append(event_info)

    sb.quit()
    return events


def extract_event_info(div, store: bool = False) -> Pokemon_Event:
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
    return Pokemon_Event(
        event_name,
        event_type,
        event_loca,
        event_date,
        logo,
        premier
    )
