import os
from src.pokemon import (
    get_decklist_png, get_decklist_pdf, convert_pdf_to_png,
    get_premier_events, get_store_events, extract_event_info
)
from unittest.mock import patch, call, MagicMock


@patch('src.pokemon.get_decklist_pdf')
@patch('src.pokemon.convert_pdf_to_png')
@patch('os.remove')
def test_get_decklist_png(mock_remove, mock_convert, mock_get_pdf):
    mock_get_pdf.return_value = None
    mock_convert.return_value = None

    get_decklist_png("test.png")

    mock_get_pdf.assert_called_once_with("tmp.pdf")
    mock_convert.assert_called_once_with("tmp.pdf", "test.png")
    mock_remove.assert_called_once_with("tmp.pdf")


@patch('shutil.rmtree')
@patch('os.rename')
@patch('os.remove')
@patch('os.path.exists')
@patch('os.listdir')
@patch('src.pokemon.Driver')
def test_get_decklist_pdf(
    mock_driver,
    mock_listdir,
    mock_exists,
    mock_remove,
    mock_rename,
    mock_rmtree
):
    mock_driver_instance = mock_driver.return_value
    elm = mock_driver_instance.cdp.find_visible_elements.return_value[0]
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        elm
    ]
    elm.get_attribute.return_value = "Play! Pokémon Deck List (A4)"
    elm.click.return_value = None

    mock_listdir.return_value = ["decklist.pdf"]
    mock_exists.return_value = True

    get_decklist_pdf("output.pdf")

    mock_driver.assert_called_once_with(
        uc=True,
        locale_code="en",
        ad_block=True,
        external_pdf=True
    )
    mock_driver_instance.uc_activate_cdp_mode.assert_called_once_with(
        (
            "https://www.pokemon.com/us/play-pokemon/"
            "about/tournaments-rules-and-resources"
        )
    )
    assert mock_driver_instance.sleep.call_count == 2
    mock_driver_instance.cdp.find_visible_elements.assert_called_once_with("a")
    elm.click.assert_called_once()
    mock_listdir.assert_called_once_with("downloaded_files")
    mock_exists.assert_has_calls([
        call(f"downloaded_files{os.sep}decklist.pdf"),
        call("output.pdf")
    ])
    mock_remove.assert_called_once_with("output.pdf")
    mock_rename.assert_called_once_with(
        f"downloaded_files{os.sep}decklist.pdf", "output.pdf"
    )
    mock_rmtree.assert_called_once_with("downloaded_files", ignore_errors=True)

    mock_listdir.return_value = ["fakefile.png"]
    try:
        get_decklist_pdf("output.pdf")
    except Exception as e:
        assert str(e) == "No pdf in downloaded files"

    elm.get_attribute.return_value = "Play! Pokémon Deck List (A2)"
    try:
        get_decklist_pdf("output.pdf")
    except Exception as e:
        assert str(e) == "Couldn't find sheet in page"


@patch('src.pokemon.fitz.open')
def test_convert_pdf_to_png(mock_fitz_open):
    mock_doc = mock_fitz_open.return_value
    mock_doc.__iter__.return_value = [mock_doc]
    mock_pix = mock_doc.get_pixmap.return_value
    mock_pix.save.return_value = None

    convert_pdf_to_png("input.pdf", "output.png")

    mock_fitz_open.assert_called_once_with("input.pdf")
    mock_doc.__iter__.assert_called_once()

    assert mock_doc.get_pixmap.call_count == 1
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
    "date": "January 14-16,2025"
}


def test_extract_event_info():
    mock_e_div = MockEventDiv(MOCK_EVENT_DATA, store=True)
    event = extract_event_info(mock_e_div, store=True)
    for k in MOCK_EVENT_DATA.keys():
        assert event[k] == MOCK_EVENT_DATA[k]


@patch('src.pokemon.extract_event_info')
@patch('src.pokemon.Driver')
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


@patch('src.pokemon.extract_event_info')
@patch('src.pokemon.Driver')
def test_get_premier_events(
    mock_driver,
    mock_extract
):
    mock_extract.return_value = MOCK_EVENT_DATA
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

    assert mock_driver_instance.sleep.call_count == 3
    assert mock_extract.call_count == 3
    mock_driver_instance.quit.assert_called_once()
    assert len(results) == 3
    assert results[0] == MOCK_EVENT_DATA
