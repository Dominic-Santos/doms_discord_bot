import fitz  # PyMuPDF
import os
from seleniumbase import Driver
import shutil

POKEMON_EVENTS_BASE_URL = "https://events.pokemon.com"
POKEMON_RULES_URL = (
    "https://www.pokemon.com/us/play-pokemon/"
    "about/tournaments-rules-and-resources"
)
POKEMON_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/LocationDetail"
POKEMON_PREMIER_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/Home"


def convert_pdf_to_png(in_file, out_file):
    doc = fitz.open(in_file)  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.0, 2.0)
        )  # render page to an image
        pix.save(out_file)


def get_decklist_pdf(output_filename):
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


def get_decklist_png(output_filename="sign_up_sheet.png"):
    get_decklist_pdf("tmp.pdf")
    convert_pdf_to_png("tmp.pdf", output_filename)
    # Clean up temporary files if necessary
    os.remove("tmp.pdf")


def get_premier_events():
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode(POKEMON_PREMIER_EVENTS_URL)
    sb.sleep(5)
    tabs = sb.cdp.find_visible_elements("button.osui-tabs__header-item")

    if len(tabs) != 3:
        raise Exception("Failed to load events page")

    tabs[1].click()
    sb.sleep(2)

    events = []

    event_divs = sb.cdp.find_visible_elements("div.map-location-card")
    for div in event_divs:
        event_info = _extract_event_info(div)
        events.append(event_info)

    sb.quit()
    return events


def get_store_events(guids=[]):
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
            event_info = _extract_event_info(div, store=True)
            events[guid].append(event_info)

    sb.quit()
    return events


def _extract_event_info(div, store=False):
    img = div.children[1].children[0].children[0].children[0]
    if store:
        img = img.children[0]

    logo = img["src"]
    base = div.children[0].children[0].children[0].children[0].children[0]
    event_type = base.children[0].children[0].text
    event_name = base.children[1].children[0].text
    event_loca = base.children[2].children[1].children[0].text
    event_date = base.children[3].children[1].children[0].text
    return {
        "logo": logo,
        "type": event_type,
        "name": event_name,
        "location": event_loca,
        "date": event_date
    }
