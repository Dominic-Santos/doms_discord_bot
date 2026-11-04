from datetime import datetime
from unittest.mock import patch, MagicMock, ANY
from src.pkmncards import (
    get_legal_card_list, save_cards_to_file,
    get_legal_cards, get_card_text, get_pokemon_sets, check_should_skip_set,
    get_set_links, get_set_card_total, get_set_cards, get_all_cards
)


def pokemon_card_mock():
    return [
        MagicMock(children=[
            MagicMock(children=[
                MagicMock(children=[
                    MagicMock(text="Set 1"),
                    MagicMock(text="001"),
                    MagicMock(
                        text="Card 1",
                        children=[
                            {"href": "https://example.com/card1"}
                        ]),
                    MagicMock(text="Type 1"),
                    MagicMock(text="Color 1"),
                    MagicMock(text="Rare")
                ])
            ])
        ])
    ]


@patch("src.pkmncards.Driver")
def test_get_card_text(mock_driver):
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        MagicMock(text="Card text here")
    ]

    card_text = get_card_text("https://example.com/card")

    mock_driver.assert_called_once_with(
        uc=True, locale_code="en", ad_block=True
    )
    mock_driver_instance.uc_activate_cdp_mode.assert_called_once_with(
        "https://example.com/card"
    )
    mock_driver_instance.sleep.assert_called_once_with(1)
    assert card_text == "Card text here"


@patch("src.pkmncards.get_legal_card_list")
@patch("src.pkmncards.save_cards_to_file")
def test_get_legal_cards(mock_save, mock_get):
    mock_get.return_value = ([
        {
            "set": "Set 1",
            "number": "001",
            "name": "Card 1",
            "type": "Type 1",
            "color": "Color 1",
            "rarity": "Rare",
            "link": "https://example.com/card1"
        }
    ], True, 1)
    get_legal_cards("test.json")
    assert mock_get.call_count == 2
    assert mock_save.call_count == 2


@patch("src.pkmncards.datetime")
@patch("src.pkmncards.get_legal_card_list")
@patch("src.pkmncards.save_cards_to_file")
def test_get_legal_cards_fail(mock_save, mock_get, mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 4, 15)
    mock_get.return_value = ([], False, 0)
    get_legal_cards("test.json")
    assert mock_get.call_count == 3
    assert mock_save.call_count == 0


@patch("builtins.open")
@patch("src.pkmncards.json.dump")
def test_save_cards_to_file(mock_dump, mock_open):
    mock_dump.return_value = None
    save_cards_to_file([{
        "set": "Set 1",
        "number": "001",
        "name": "Card 1",
        "type": "Type 1",
        "color": "Color 1",
        "rarity": "Rare",
        "link": "https://example.com/card1"
    }], 1, "test.json")
    mock_dump.assert_called_once_with({
        "cards": {
            "Set 1": {
                "001": {
                    "name": "Card 1",
                    "type": "Type 1",
                    "color": "Color 1",
                    "rarity": "Rare",
                    "link": "https://example.com/card1"
                }
            }
        },
        "count": 1
    }, mock_open.return_value, indent=4)


@patch("src.pkmncards.Driver")
def test_get_legal_card_list(mock_driver):
    value_max = 262

    class MockFindVisibleElements:
        def __init__(self):
            self.counter = 0
            self.v_max = value_max
            self.empty = True

        def __call__(self, selector):
            if selector == "article.type-pkmn_card":
                return pokemon_card_mock()
            elif selector == "li.next-link a":
                return [MagicMock()]
            elif selector == "span.range-current":
                v_from = 200 * self.counter
                v_to = min(200 * (self.counter + 1), self.v_max)
                self.counter += 1
                return [
                    MagicMock(
                        text=f"{v_from} thru {v_to}"
                    )
                ]
            elif selector == "span.out-of":
                return [
                    MagicMock(
                        children=[
                            MagicMock(
                                text=f"/ {self.v_max}"
                            )
                        ]
                    )
                ]
            elif selector == "li.results":
                if self.empty:
                    return [
                        MagicMock(
                            children=[
                                MagicMock(
                                    text="no results"
                                )
                            ]
                        )
                    ]
                return [
                    MagicMock(
                        children=[
                            MagicMock(
                                text="1 thru 2"
                            )
                        ]
                    )
                ]

    mock_elements = MockFindVisibleElements()
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements = mock_elements
    cards, valid, count = get_legal_card_list("", 0)

    assert len(cards) == 0
    assert not valid
    assert count == 0
    mock_driver_instance.sleep.assert_called_once()
    mock_driver_instance.uc_activate_cdp_mode.assert_called_once()
    mock_driver_instance.quit.assert_called_once()
    mock_driver.assert_called_once_with(
        uc=True, locale_code="en", ad_block=True
    )

    mock_elements.empty = False
    cards, valid, count = get_legal_card_list("", 0)

    assert valid
    assert count == value_max
    assert len(cards) == 2
    assert cards[0]["set"] == "Set 1"
    assert cards[0]["number"] == "001"
    assert cards[0]["name"] == "Card 1"
    assert cards[0]["type"] == "Type 1"
    assert cards[0]["color"] == "Color 1"
    assert cards[0]["rarity"] == "Rare"
    assert cards[0]["link"] == "https://example.com/card1"
    assert mock_driver_instance.uc_activate_cdp_mode.call_count == 2
    assert mock_driver_instance.sleep.call_count == 3
    assert mock_driver_instance.quit.call_count == 2
    assert mock_elements.counter == 2

    cards, valid, count = get_legal_card_list("", value_max)
    assert len(cards) == 0
    assert valid
    assert count == value_max
    assert mock_driver_instance.sleep.call_count == 4


@patch("builtins.open")
@patch("src.pkmncards.json.dump")
@patch("src.pkmncards.Driver")
def test_get_pokemon_sets(
    mock_driver, mock_dump, mock_open
):
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        MagicMock(text="Destined Rivals (DRI)"),
        MagicMock(text="Journey Together (JTG)"),
        MagicMock(text="Prismatic Evolutions (PRE)"),
        MagicMock(text="Fake Set"),
        MagicMock(text="Miscellaneous")
    ]

    get_pokemon_sets()
    mock_dump.assert_called_once_with({
        "black star promo": "SMP",
        "destined rivals": "DRI",
        "journey together": "JTG",
        "prismatic evolutions": "PRE",
        "Fake Set": "Fake Set"
    }, ANY, indent=4)
    mock_driver_instance.quit.assert_called_once()


def test_check_should_skip_set():
    assert check_should_skip_set("Shield & Sword Energy") == (False, False)
    assert check_should_skip_set("Miscellaneous") == (True, False)
    assert check_should_skip_set("Fake Set") == (False, False)
    assert check_should_skip_set("Destined Rivals (DRI)") == (False, True)


class LinkElement:
    def __init__(self, text, href):
        self.text = text
        self.href = href

    def __getitem__(self, key):
        return self.href


@patch("src.pkmncards.Driver")
def test_get_set_links(mock_driver):
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        LinkElement("Destined Rivals (DRI)", "https://example.com/dri/"),
        LinkElement("Fake Set", "https://example.com/fake/"),
        LinkElement("Miscellaneous", "https://example.com/misc/"),
    ]

    assert get_set_links() == {
        "DRI": "https://example.com/dri/",
        "Fake Set": "https://example.com/fake/",
    }
    mock_driver_instance.quit.assert_called_once()


def test_get_set_card_total():
    sb = MagicMock()
    no_results = MagicMock(children=[MagicMock(text="No Results")])
    sb.cdp.find_visible_elements.return_value = [no_results]
    assert get_set_card_total(sb, "https://example.com/set/?display=list") == 0
    sb.cdp.open.assert_called_once_with("https://example.com/set/?display=list")

    results = MagicMock(children=[MagicMock(text="Results")])
    total = MagicMock(children=[MagicMock(text="/ 1,234")])
    sb.cdp.find_visible_elements.side_effect = [[results], [total]]
    assert get_set_card_total(sb, "https://example.com/set/?display=list") == 1234


def test_get_set_cards_multiple_pages():
    sb = MagicMock()
    second_card = pokemon_card_mock()
    second_card[0].children[0].children[0].children[1].text = "002"
    elements = {
        "span.range-current": [
            [MagicMock(text="1 thru 1")], [MagicMock(text="2")]
        ],
        "article.type-pkmn_card": [pokemon_card_mock(), second_card],
        "li.next-link a": [[MagicMock()]],
    }
    sb.cdp.find_visible_elements.side_effect = (
        lambda query: elements[query].pop(0)
    )

    cards = get_set_cards(sb, 2)

    assert list(cards.keys()) == ["001", "002"]
    assert cards["001"] == {
        "name": "Card 1",
        "type": "Type 1",
        "color": "Color 1",
        "rarity": "Rare",
        "link": "https://example.com/card1",
    }


@patch("src.pkmncards.get_set_cards")
@patch("src.pkmncards.get_set_card_total")
@patch("src.pkmncards.get_set_links")
@patch("src.pkmncards.Driver")
@patch("src.pkmncards.json")
@patch("builtins.open")
def test_get_all_cards(
    mock_open, mock_json, mock_driver, mock_links, mock_total, mock_cards
):
    mock_json.load.return_value = {"cards": {
        "SAME": {"1": {}},
        "CHANGED": {"1": {}},
    }}
    mock_links.return_value = {
        "SAME": "https://example.com/same/",
        "CHANGED": "https://example.com/changed/",
        "NEW": "https://example.com/new/",
        "EMPTY": "https://example.com/empty/",
    }
    mock_total.side_effect = [1, 2, 1, 0]
    mock_cards.side_effect = [{"1": {}, "2": {}}, {"1": {}}]

    get_all_cards("cards.json")

    assert mock_cards.call_count == 2
    saved = mock_json.dump.call_args[0][0]["cards"]
    assert set(saved.keys()) == {"SAME", "CHANGED", "NEW"}
    assert len(saved["CHANGED"]) == 2
    assert mock_json.dump.call_count == 2
    mock_driver.return_value.quit.assert_called_once()


@patch("src.pkmncards.get_set_cards")
@patch("src.pkmncards.get_set_card_total")
@patch("src.pkmncards.get_set_links")
@patch("src.pkmncards.Driver")
@patch("src.pkmncards.json")
@patch("builtins.open")
def test_get_all_cards_without_existing_file(
    mock_open, mock_json, mock_driver, mock_links, mock_total, mock_cards
):
    mock_json.load.side_effect = Exception("missing")
    mock_links.return_value = {"NEW": "https://example.com/new/"}
    mock_total.return_value = 1
    mock_cards.return_value = {"1": {}}

    get_all_cards("cards.json")

    mock_json.dump.assert_called_once_with(
        {"cards": {"NEW": {"1": {}}}}, ANY, indent=4
    )
