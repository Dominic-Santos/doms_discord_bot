from src.pokemon import (
    get_decklist_png, get_decklist_pdf, convert_pdf_to_png,
    get_premier_events, get_store_events, extract_event_info,
    PokemonEvent, get_logo
)
from src.core import DATA_FOLDER
import pytest
from unittest.mock import patch, MagicMock, mock_open


@patch("src.pokemon.get_decklist_pdf")
@patch("src.pokemon.convert_pdf_to_png")
@patch("os.remove")
def test_get_decklist_png(mock_remove, mock_convert, mock_get_pdf):
    mock_get_pdf.return_value = None
    mock_convert.return_value = None

    png_file = "test.png"
    pdf_file = f"{DATA_FOLDER}/tmp.pdf"

    get_decklist_png(png_file)

    mock_get_pdf.assert_called_once_with(pdf_file)
    mock_convert.assert_called_once_with(pdf_file, png_file)
    mock_remove.assert_called_once_with(pdf_file)


PAGE = (
    '<a href="/sheets/us.pdf">Play! Pok&eacute;mon Deck List (8.5x11)</a>'
    '<a href="/sheets/a4.pdf" target="_blank">'
    "Play! Pok&eacute;mon Deck List (A4)</a>"
)


def mock_response(text="", content=b""):
    response = MagicMock(text=text, content=content)
    return response


@patch("src.pokemon.requests.get")
def test_get_decklist_pdf(mock_get):
    mock_get.side_effect = [
        mock_response(text=PAGE), mock_response(content=b"%PDF-1.4 data")
    ]
    m = mock_open()
    with patch("builtins.open", m):
        get_decklist_pdf("output.pdf")

    assert mock_get.call_args_list[1][0][0] == (
        "https://www.pokemon.com/sheets/a4.pdf"
    )
    assert mock_get.call_args_list[1][1]["headers"]["Referer"] == (
        "https://www.pokemon.com/us/play-pokemon/"
        "about/tournaments-rules-and-resources"
    )
    m.assert_called_once_with("output.pdf", "wb")
    m().write.assert_called_once_with(b"%PDF-1.4 data")


@patch("src.pokemon.requests.get")
def test_get_decklist_pdf_errors(mock_get):
    mock_get.side_effect = [mock_response(text="<a href='/x'>Other</a>")]
    with pytest.raises(Exception, match="Couldn't find sheet in page"):
        get_decklist_pdf("output.pdf")

    mock_get.side_effect = [
        mock_response(text=PAGE), mock_response(content=b"<html>blocked")
    ]
    with patch("builtins.open", mock_open()) as m:
        with pytest.raises(Exception, match="not a pdf"):
            get_decklist_pdf("output.pdf")
    m.assert_not_called()


@patch("src.pokemon.fitz.open")
def test_convert_pdf_to_png(mock_fitz_open):
    mock_doc = mock_fitz_open.return_value
    mock_doc.__iter__.return_value = [mock_doc]
    mock_pix = mock_doc.get_pixmap.return_value
    mock_pix.save.return_value = None

    convert_pdf_to_png("input.pdf", "output.png")

    mock_fitz_open.assert_called_once_with("input.pdf")
    mock_doc.__iter__.assert_called_once()

    mock_doc.get_pixmap.assert_called_once()
    mock_pix.save.assert_called_once_with("output.png")


class MockEventDiv:
    def __init__(self, data={}, store=False):
        img_head = MagicMock()
        base_head = MagicMock()
        self.children = [base_head, img_head]

        img_children = 2
        if store:
            img_children += 1

        for _ in range(img_children):
            img_head.children = [MagicMock()]
            img_head = img_head.children[0]
        img_head.children = [{"src": data.get("logo", "logo")}]

        base_children = 4
        for _ in range(base_children):
            base_head.children = [MagicMock()]
            base_head = base_head.children[0]

        base_head.children = [
            MagicMock(children=[MagicMock(text=data.get("type", "type"))]),
            MagicMock(children=[MagicMock(text=data.get("name", "name"))]),
            MagicMock(children=[
                None,
                MagicMock(children=[
                    MagicMock(text=data.get("location", "location"))
                ])
            ]),
            MagicMock(children=[
                None,
                MagicMock(children=[
                    MagicMock(text=data.get("date", "date"))
                ])
            ])
        ]


MOCK_EVENT_DATA = {
    "logo": "test.png",
    "type": "friendly",
    "name": "test event",
    "location": "hell",
    "date": "Friday, Oct 10 - Sunday, 12, 2025"
}

MOCK_EVENT = PokemonEvent(
    MOCK_EVENT_DATA["name"],
    MOCK_EVENT_DATA["type"],
    MOCK_EVENT_DATA["location"],
    MOCK_EVENT_DATA["date"],
    MOCK_EVENT_DATA["logo"],
    False
)

MOCK_ONE_DAY_EVENT_DATA = {
    "logo": "test.png",
    "type": "friendly",
    "name": "test event",
    "location": "hell",
    "date": "Wednesday, September 24, 2025 03:00 PM"
}

MOCK_ONE_DAY_EVENT = PokemonEvent(
    MOCK_ONE_DAY_EVENT_DATA["name"],
    MOCK_ONE_DAY_EVENT_DATA["type"],
    MOCK_ONE_DAY_EVENT_DATA["location"],
    MOCK_ONE_DAY_EVENT_DATA["date"],
    MOCK_ONE_DAY_EVENT_DATA["logo"],
    False
)

MOCK_BETWEEN_MONTHS_EVENT_DATA = {
    "logo": "test.png",
    "type": "friendly",
    "name": "test event",
    "location": "hell",
    "date": "Friday, Oct 10 - Sunday, Nov 12, 2025"
}

MOCK_BETWEEN_MONTHS_EVENT = PokemonEvent(
    MOCK_BETWEEN_MONTHS_EVENT_DATA["name"],
    MOCK_BETWEEN_MONTHS_EVENT_DATA["type"],
    MOCK_BETWEEN_MONTHS_EVENT_DATA["location"],
    MOCK_BETWEEN_MONTHS_EVENT_DATA["date"],
    MOCK_BETWEEN_MONTHS_EVENT_DATA["logo"],
    False
)


def test_extract_event_info():
    mock_e_div = MockEventDiv(MOCK_EVENT_DATA, store=True)
    event = extract_event_info(mock_e_div, store=True)
    event.logo == MOCK_EVENT_DATA["logo"]
    event.name == MOCK_EVENT_DATA["name"]
    event.type == MOCK_EVENT_DATA["type"]
    event.location == MOCK_EVENT_DATA["location"]
    event.start_date.day == 10
    event.start_date.month == 10
    event.start_date.year == 2025
    event.end_date.day == 13
    event.end_date.month == 10
    event.end_date.year == 2025


def test_extract_one_day_event_info():
    mock_e_div = MockEventDiv(MOCK_ONE_DAY_EVENT_DATA, store=True)
    event = extract_event_info(mock_e_div, store=True)
    event.logo == MOCK_ONE_DAY_EVENT_DATA["logo"]
    event.name == MOCK_ONE_DAY_EVENT_DATA["name"]
    event.type == MOCK_ONE_DAY_EVENT_DATA["type"]
    event.location == MOCK_ONE_DAY_EVENT_DATA["location"]
    event.start_date.day == 24
    event.start_date.month == 10
    event.start_date.year == 2025
    event.end_date.day == 25
    event.end_date.month == 10
    event.end_date.year == 2025


def test_extract_between_months_event_info():
    mock_e_div = MockEventDiv(MOCK_BETWEEN_MONTHS_EVENT_DATA, store=True)
    event = extract_event_info(mock_e_div, store=True)
    event.logo == MOCK_BETWEEN_MONTHS_EVENT_DATA["logo"]
    event.name == MOCK_BETWEEN_MONTHS_EVENT_DATA["name"]
    event.type == MOCK_BETWEEN_MONTHS_EVENT_DATA["type"]
    event.location == MOCK_BETWEEN_MONTHS_EVENT_DATA["location"]
    event.start_date.day == 10
    event.start_date.month == 10
    event.start_date.year == 2025
    event.end_date.day == 13
    event.end_date.month == 11
    event.end_date.year == 2025


@patch("src.pokemon.extract_event_info")
@patch("src.pokemon.Driver")
def test_get_store_events(
    mock_driver,
    mock_extract
):
    mock_extract.return_value = MOCK_EVENT_DATA

    result = get_store_events()
    assert len(result) == 0

    mock_driver_instance = mock_driver.return_value
    mock = [MagicMock(
        children=[
            MagicMock(
                children=[MagicMock()]
            )
        ]
    )]
    mock_driver_instance.cdp.find_visible_elements.return_value = mock
    result = get_store_events(["fake_guid"])
    mock_driver_instance.uc_activate_cdp_mode.assert_called_once()
    mock_driver_instance.sleep.assert_called_once()
    mock_driver_instance.quit.assert_called_once()


@patch("src.pokemon.extract_event_info")
@patch("src.pokemon.Driver")
def test_get_premier_events(
    mock_driver,
    mock_extract
):
    mock_extract.return_value = MOCK_EVENT
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        MagicMock()
    ]

    try:
        _ = get_premier_events()
    except Exception as e:
        assert str(e) == "Failed to load events page"

    mock_driver_instance.uc_activate_cdp_mode.assert_called_once()
    mock_driver_instance.sleep.assert_called_once()

    mock_driver_instance.cdp.find_visible_elements.return_value = [
        MagicMock(), MagicMock(), MagicMock()
    ]

    results = get_premier_events()

    mock_driver_instance.quit.assert_called_once()
    assert len(results) == 3
    assert results[0].name == MOCK_EVENT.name


@patch("builtins.open")
@patch("src.pokemon.urlretrieve")
@patch("src.pokemon.requests.get")
def test_get_logo(mock_get, mock_retrieve, mock_open):
    vector_img = "data:image/gif;base64,randomstringofletters"
    other_img = "logo.png"

    mock_retrieve.return_value = ("filename", None)
    mock_get.return_value = MagicMock(
        content="contenttest",
        status_code=200
    )
    mock_open.return_value = MagicMock(
        read=MagicMock(return_value="readtest")
    )

    logo = get_logo(vector_img)
    assert logo == "readtest"

    logo = get_logo(other_img)
    assert logo == "contenttest"
