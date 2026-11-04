import fitz  # PyMuPDF
import os
from seleniumbase import Driver
from datetime import datetime, timedelta
import html
import json
import re
from urllib.parse import urljoin
from urllib.request import urlretrieve
import requests
from .core import DATA_FOLDER

POKEMON_EVENTS_BASE_URL = "https://events.pokemon.com"
POKEMON_RULES_URL = (
    "https://www.pokemon.com/us/play-pokemon/"
    "about/tournaments-rules-and-resources"
)
POKEMON_PREMIER_EVENTS_URL = f"{POKEMON_EVENTS_BASE_URL}/EventLocator/Home"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 60
DECKLIST_LINK_TEXT = "Play! Pokémon Deck List (A4)"
DECKLIST_LINK = re.compile(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
EVENT_DATE_FORMAT = "%Y-%m-%d"
EVENT_LOCATOR_PAGE_LOAD_TIME = 10
EVENT_LOCATOR_DAYS_AHEAD = 365
# Runs inside the browser so the request carries the cookies that passed the
# site's bot check. The api version changes on every deploy, so it is read
# from the screen's own script instead of being hardcoded.
EVENT_LOCATOR_SCRIPT = """
const [view, action, variables, clientVariables, done] = arguments;
(async () => {
  const base = "/EventLocator";
  const get = async (path) => (await fetch(base + path)).text();
  const token = JSON.parse(await get("/moduleservices/moduleversioninfo"))
    .versionToken;
  const code = await get("/scripts/EventLocator." + view + ".mvc.js");
  const api = new RegExp(
    '"' + action + '"\\\\s*,\\\\s*"[^"]+"\\\\s*,\\\\s*"([^"]+)"'
  ).exec(code);
  const cookie = decodeURIComponent(
    (document.cookie.match(/nr2Users=([^;]+)/) || [, ""])[1]
  );
  const response = await fetch(
    base + "/screenservices/EventLocator/" + view.replace(".", "/") +
      "/" + action,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json",
        "X-CSRFToken": (cookie.match(/crf=([^;]*)/) || [, ""])[1],
      },
      body: JSON.stringify({
        versionInfo: {moduleVersion: token, apiVersion: api && api[1]},
        viewName: view,
        screenData: {variables},
        clientVariables,
      }),
    }
  );
  done({status: response.status, body: await response.text()});
})().catch((error) => done({status: 0, body: String(error)}));
"""
TMP_FILE = f"{DATA_FOLDER}/tmp.pdf"


class PokemonEvent():
    def __init__(
        self,
        name: str,
        type: str,
        location: str,
        start_date: datetime,
        end_date: datetime,
        logo: str,
        premier: bool
    ):
        self.name = name
        self.type = type
        self.location = location
        self.logo = logo
        self.premier = premier

        self.start_date = start_date
        # end_date is the last day of the event, discord wants the day after
        self.end_date = end_date + timedelta(days=1)


def convert_pdf_to_png(in_file: str, out_file: str):
    doc = fitz.open(in_file)  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.0, 2.0)
        )  # render page to an image
        pix.save(out_file)


def get_decklist_pdf(output_filename: str):
    # the site rejects requests that don't look like a browser
    page = requests.get(
        POKEMON_RULES_URL, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT
    )
    page.raise_for_status()

    for href, text in DECKLIST_LINK.findall(page.text):
        if html.unescape(text).strip() == DECKLIST_LINK_TEXT:
            break
    else:
        raise Exception("Couldn't find sheet in page")

    pdf = requests.get(
        urljoin(POKEMON_RULES_URL, html.unescape(href)),
        headers={**BROWSER_HEADERS, "Referer": POKEMON_RULES_URL},
        timeout=REQUEST_TIMEOUT,
    )
    pdf.raise_for_status()
    if not pdf.content.startswith(b"%PDF"):
        raise Exception("Downloaded sheet is not a pdf")

    with open(output_filename, "wb") as f:
        f.write(pdf.content)


def get_decklist_png(output_filename: str = "sign_up_sheet.png"):
    get_decklist_pdf(TMP_FILE)
    convert_pdf_to_png(TMP_FILE, output_filename)
    # Clean up temporary files if necessary
    os.remove(TMP_FILE)


def parse_event_date(date: str) -> datetime:
    return datetime.strptime(date[:10], EVENT_DATE_FORMAT)


def open_event_locator() -> Driver:
    # the site only serves its data to a browser that passed its bot check
    driver = Driver(uc=True, headless=True, locale_code="en", ad_block=True)
    driver.set_script_timeout(REQUEST_TIMEOUT)
    driver.uc_open_with_reconnect(
        POKEMON_PREMIER_EVENTS_URL, EVENT_LOCATOR_PAGE_LOAD_TIME
    )
    return driver


def call_event_locator(
    driver: Driver, view: str, action: str, variables: dict
) -> dict:
    today = datetime.now()
    end = today + timedelta(days=EVENT_LOCATOR_DAYS_AHEAD)
    client_variables = {
        "StartDate": today.strftime(EVENT_DATE_FORMAT),
        "EndDate": end.strftime(EVENT_DATE_FORMAT),
        "MaxDateLimit": EVENT_LOCATOR_DAYS_AHEAD,
        "LocaleHeader": "en",
        "UserLocale": "en",
        "OldUserLocale": "en",
        "LocaleFooter": "en",
        "IsShowEvents": True,
        "IsOnReadyFinished": True,
        "CurrTab": 1,
    }
    result = driver.execute_async_script(
        EVENT_LOCATOR_SCRIPT, view, action, variables, client_variables
    )

    if result["status"] != 200:
        raise Exception(f"Failed to load events: {result['body'][:200]}")

    response = json.loads(result["body"])
    if "exception" in response:
        raise Exception(
            f"Failed to load events: {response['exception']['message']}"
        )
    return response["data"]


def get_premier_events() -> list[PokemonEvent]:
    driver = open_event_locator()
    try:
        data = call_event_locator(
            driver,
            "MainFlow.Home",
            "DataActionGetPremierEventsByStartDate",
            {"locale": "en"}
        )
    finally:
        driver.quit()

    return [
        PokemonEvent(
            event["Name"],
            event["EventType"],
            ", ".join(filter(None, [event["City"], event["Country"]])),
            parse_event_date(event["StartDate"]),
            parse_event_date(event["EndDate"]),
            f"/EventLocator/img/EventLocator.{event['Badge']}.png",
            True
        )
        for event in data["List"]["List"]
    ]


def get_store_events(guids: list[str] = []) -> dict[str, list[PokemonEvent]]:
    if len(guids) == 0:
        return {}

    events = {}
    driver = open_event_locator()
    try:
        for guid in guids:
            data = call_event_locator(
                driver,
                "MainFlow.LocationDetail",
                "DataActionGetEventsByGUID",
                {"locale": "en", "LocationGuid": guid, "EventDetailGUID": guid}
            )
            events[guid] = [
                PokemonEvent(
                    item["Events"]["Name"],
                    item["EventTypeName"],
                    item["Events"]["Address"]["Full_address"],
                    parse_event_date(item["Events"]["Start_date"]),
                    parse_event_date(item["Events"]["Start_date"]),
                    item["EventBadge"],
                    False
                )
                for item in data["Result"]["List"]
            ]
    finally:
        driver.quit()

    return events


def get_logo(url: str) -> bytes:
    if ";base64," in url:
        filename, _ = urlretrieve(url)
        f = open(filename, "rb")
        return f.read()

    full_url = f"{POKEMON_EVENTS_BASE_URL}{url}"
    response = requests.get(full_url)

    if response.status_code == 200:
        return response.content
