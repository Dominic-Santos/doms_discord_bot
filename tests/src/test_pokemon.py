from src.pokemon import (
    get_decklist_png, get_decklist_pdf, convert_pdf_to_png,
    get_premier_events, get_store_events, open_event_locator,
    call_event_locator, parse_event_date, PokemonEvent, get_logo
)
from src.core import DATA_FOLDER
from datetime import datetime
import json
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


def mock_event_locator(driver, *responses):
    driver.execute_async_script.side_effect = [
        {"status": 200, "body": json.dumps(response)}
        for response in responses
    ]


def test_parse_event_date():
    assert parse_event_date("2026-11-09T18:30:00Z") == datetime(2026, 11, 9, 18, 30)
    assert parse_event_date("2026-11-14") == datetime(2026, 11, 14)


def test_event_end_date_is_the_day_after():
    event = PokemonEvent(
        "a", "b", "c", datetime(2026, 10, 10), datetime(2026, 10, 12), "d", True
    )
    assert event.start_date == datetime(2026, 10, 10)
    assert event.end_date == datetime(2026, 10, 13)


@patch("src.pokemon.Driver")
def test_open_event_locator(mock_driver):
    driver = open_event_locator()

    assert driver == mock_driver.return_value
    assert mock_driver.call_args.kwargs["headless"] is True
    driver.uc_open_with_reconnect.assert_called_once()


def test_call_event_locator():
    driver = MagicMock()
    mock_event_locator(driver, {"data": {"a": 1}})

    assert call_event_locator(driver, "view", "action", {"b": 2}) == {"a": 1}

    args = driver.execute_async_script.call_args.args
    assert args[1:4] == ("view", "action", {"b": 2})
    assert args[4]["MaxDateLimit"] == 365


def test_call_event_locator_errors():
    driver = MagicMock()
    driver.execute_async_script.return_value = {"status": 403, "body": "no"}
    with pytest.raises(Exception, match="Failed to load events: no"):
        call_event_locator(driver, "view", "action", {})

    mock_event_locator(
        driver, {"exception": {"message": "Invalid Login"}, "data": {}}
    )
    with pytest.raises(Exception, match="Invalid Login"):
        call_event_locator(driver, "view", "action", {})


@patch("src.pokemon.open_event_locator")
def test_get_premier_events(mock_open_locator):
    driver = mock_open_locator.return_value
    mock_event_locator(driver, {"data": {"List": {"List": [
        {
            "Name": "Big Event",
            "EventType": "Regional Championships",
            "City": "Stuttgart",
            "Country": "Germany",
            "StartDate": "2026-11-28",
            "EndDate": "2026-11-29",
            "Badge": "RegionalsBadge",
        },
        {
            "Name": "Online Event",
            "EventType": "Special",
            "City": "",
            "Country": "Germany",
            "StartDate": "2026-12-01",
            "EndDate": "2026-12-01",
            "Badge": "WorldsBadge",
        },
    ]}}})

    events = get_premier_events()

    assert len(events) == 2
    assert events[0].name == "Big Event"
    assert events[0].type == "Regional Championships"
    assert events[0].location == "Stuttgart, Germany"
    assert events[0].start_date == datetime(2026, 11, 28)
    assert events[0].end_date == datetime(2026, 11, 30)
    assert events[0].logo == "/EventLocator/img/EventLocator.RegionalsBadge.png"
    assert events[0].premier is True
    assert events[1].location == "Germany"
    driver.quit.assert_called_once()


@patch("src.pokemon.open_event_locator")
def test_get_premier_events_quits_on_error(mock_open_locator):
    driver = mock_open_locator.return_value
    driver.execute_async_script.return_value = {"status": 0, "body": "boom"}

    with pytest.raises(Exception, match="boom"):
        get_premier_events()

    driver.quit.assert_called_once()


@patch("src.pokemon.open_event_locator")
def test_get_store_events(mock_open_locator):
    assert get_store_events() == {}
    mock_open_locator.assert_not_called()

    driver = mock_open_locator.return_value
    mock_event_locator(
        driver,
        {"data": {"Result": {"List": [{
            "Events": {
                "Name": "Game Night",
                "Start_date": "2026-11-09T18:30:00Z",
                "Address": {"Full_address": "1 Some Road, London"},
            },
            "EventTypeName": "Friendly Tournament",
            "EventBadge": "/OPPlayerApp/img/badge.png",
        }]}}},
        {"data": {"Result": {"List": []}}},
    )

    events = get_store_events(["guid-1", "guid-2"])

    assert list(events) == ["guid-1", "guid-2"]
    assert events["guid-2"] == []
    event = events["guid-1"][0]
    assert event.name == "Game Night"
    assert event.type == "Friendly Tournament"
    assert event.location == "1 Some Road, London"
    assert event.start_date == datetime(2026, 11, 9, 18, 30)
    assert event.end_date == datetime(2026, 11, 9, 19, 30)
    assert event.logo == "/OPPlayerApp/img/badge.png"
    assert event.premier is False
    driver.quit.assert_called_once()


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
