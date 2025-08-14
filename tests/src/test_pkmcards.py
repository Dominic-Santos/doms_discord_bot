from unittest.mock import patch, MagicMock
from src.pkmncards import (
    get_legal_card_list, save_cards_to_file, get_legal_cards, get_card_text
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


@patch('src.pkmncards.Driver')
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


@patch('src.pkmncards.get_legal_card_list')
@patch('src.pkmncards.save_cards_to_file')
def test_get_legal_cards(mock_save, mock_get):
    mock_get.return_value = [
        {
            "set": "Set 1",
            "number": "001",
            "name": "Card 1",
            "type": "Type 1",
            "color": "Color 1",
            "rarity": "Rare",
            "link": "https://example.com/card1"
        }
    ]
    get_legal_cards("test.json")
    mock_get.assert_called_once()
    mock_save.assert_called_once_with(mock_get.return_value, "test.json")


@patch('builtins.open')
@patch('src.pkmncards.json.dump')
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
    }], "test.json")
    mock_dump.assert_called_once_with({
        "Set 1": {
            "001": {
                "name": "Card 1",
                "type": "Type 1",
                "color": "Color 1",
                "rarity": "Rare",
                "link": "https://example.com/card1"
            }
        }
    }, mock_open.return_value, indent=4)


@patch('src.pkmncards.Driver')
def test_get_legal_card_list(mock_driver):
    class MockFindVisibleElements:
        def __init__(self):
            self.counter = 0

        def __call__(self, selector):
            if selector == "article.type-pkmn_card":
                if self.counter != 0:
                    return pokemon_card_mock()
                return []
            elif selector == "li.next-link a":
                if self.counter == 0:
                    self.counter += 1
                    return [MagicMock()]
                else:
                    raise Exception("No more pages")

    mock_elements = MockFindVisibleElements()
    mock_driver_instance = mock_driver.return_value
    mock_driver_instance.cdp.find_visible_elements = mock_elements

    cards = get_legal_card_list()

    assert len(cards) == 1
    assert cards[0]["set"] == "Set 1"
    assert cards[0]["number"] == "001"
    assert cards[0]["name"] == "Card 1"
    assert cards[0]["type"] == "Type 1"
    assert cards[0]["color"] == "Color 1"
    assert cards[0]["rarity"] == "Rare"
    assert cards[0]["link"] == "https://example.com/card1"
    mock_driver.assert_called_once_with(
        uc=True, locale_code="en", ad_block=True
    )
    mock_driver_instance.uc_activate_cdp_mode.assert_called_once()
    assert mock_driver_instance.sleep.call_count == 2
    mock_driver_instance.quit.assert_called_once()
    assert mock_elements.counter == 1
