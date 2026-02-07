import json
from unittest.mock import patch, MagicMock
from src.core import (
    validate_decklist, fill_sheet, load_card_database,
    get_offset, convert_banned_cards
)


def test_load_card_database_not_json():
    try:
        load_card_database("tests/data/invalid_format.txt")
    except ValueError as e:
        assert str(e) == "Filename must be a JSON file."


@patch("builtins.open")
def test_load_card_database_invalid_json(mock_open):
    mock_open.side_effect = [
        MagicMock(read=MagicMock(return_value="invalid json"))
    ]
    try:
        load_card_database("tests/data/invalid_format.json")
    except ValueError as e:
        assert str(e) == "Error loading JSON file."


def test_load_card_database():
    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    all_pokemon = [p for set in pokemon for p in pokemon[set]]
    assert len(all_pokemon) == 484
    assert len(trainers.keys()) == 14
    assert len(energies.keys()) == 2
    assert count == 123


def test_load_card_database_with_banned_sets():
    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json",
        banned_sets=["BLK"]
    )
    all_pokemon = [p for set in pokemon for p in pokemon[set]]
    assert len(all_pokemon) == 323
    assert len(trainers.keys()) == 14
    assert len(energies.keys()) == 2
    assert count == 123


def test_validate_decklist_60_cards():
    decklist = {}
    valid, error = validate_decklist(decklist)
    assert valid is False
    assert error == "Decklist must contain exactly 60 cards."


def test_validate_decklist_at_least_1_pokemon():
    decklist = {
        "energies": {
            "fire energy": {"quantity": 60}
        }
    }
    valid, error = validate_decklist(decklist)
    assert valid is False
    assert error == "Decklist must contain at least 1 Pokémon."


def test_validate_decklist_max_4_copies():
    decklist = {
        "pokemon": [
            {"name": "pikachu", "quantity": 1}
        ],
        "energies": {
            "fire energy": {"quantity": 53}
        },
        "trainers": {
            "boss orders": {"quantity": 6}
        }
    }
    valid, error = validate_decklist(decklist)
    assert valid is False
    assert error == "Card boss orders exceeds the maximum of 4 copies."


def test_validate_decklist_one_ace_spec():
    decklist = {
        "pokemon": [
            {"name": "pikachu", "quantity": 1}
        ],
        "energies": {
            "fire energy": {"quantity": 53}
        },
        "trainers": {
            "boss orders": {"quantity": 4},
            "Ignition Energy": {"quantity": 2}
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )

    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Decklist can only contain one Ace Spec card."


def test_validate_decklist_illegal_card():
    decklist = {
        "pokemon": [
            {"name": "pikachu", "quantity": 1, "set": "blah", "number": 1}
        ],
        "energies": {
            "fire energy": {"quantity": 54}
        },
        "trainers": {
            "boss orders": {"quantity": 4},
            "Ignition Energy": {"quantity": 1}
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )

    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Card pikachu from set blah is not legal."


def test_validate_decklist_at_least_1_basic():
    decklist = {
        "pokemon": [
            {"name": "Swadloon", "quantity": 1, "set": "WHT", "number": "88"}
        ],
        "energies": {
            "fire energy": {"quantity": 54}
        },
        "trainers": {
            "boss orders": {"quantity": 4},
            "Ignition Energy": {"quantity": 1}
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Decklist must contain at least one Basic Pokémon."


def test_validate_decklist_check_legal_trainers():
    decklist = {
        "pokemon": [
            {"name": "Sewaddle", "quantity": 1, "set": "WHT", "number": "87"}
        ],
        "energies": {
            "fire energy": {"quantity": 54}
        },
        "trainers": {
            "boss orders": {"quantity": 4},
            "Ignition Energy": {"quantity": 1}
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Trainer card boss orders is not legal."


def test_validate_decklist_check_legal_enerigies():
    decklist = {
        "pokemon": [
            {"name": "Sewaddle", "quantity": 1, "set": "WHT", "number": "87"}
        ],
        "energies": {
            "fire energy": {"quantity": 58},
            "fake energy": {"quantity": 1}
        },
        "trainers": {
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Energy card fake energy is not legal."


def test_validate_banned_cards():
    decklist = {
        "pokemon": [
            {"name": "Sewaddle", "quantity": 1, "set": "WHT", "number": "87"}
        ],
        "energies": {
            "fire energy": {"quantity": 57},
            "Prism Energy": {"quantity": 1}
        },
        "trainers": {
            "Tool Scrapper": {"quantity": 1}
        }
    }
    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }

    banned_cards = {
        "pokemon": {"WHT": ["87"]},
        "trainers": ["Tool Scrapper"],
        "energies": ["Prism Energy"]
    }

    valid, error = validate_decklist(
        decklist, legal_cards=legalcards, banned_cards=banned_cards
    )
    assert valid is False
    assert error == "Card Sewaddle from set WHT is banned."

    banned_cards["pokemon"] = {}
    valid, error = validate_decklist(
        decklist, legal_cards=legalcards, banned_cards=banned_cards
    )
    assert valid is False
    assert error == "Trainer card Tool Scrapper is banned."

    banned_cards["trainers"] = []
    valid, error = validate_decklist(
        decklist, legal_cards=legalcards, banned_cards=banned_cards
    )
    assert valid is False
    assert error == "Energy card Prism Energy is banned."


def test_validate_decklist():
    decklist = {
        "pokemon": [
            {"name": "Sewaddle", "quantity": 1, "set": "WHT", "number": "87"}
        ],
        "energies": {
            "fire energy": {"quantity": 58},
        },
        "trainers": {
            "Tool Scrapper": {"quantity": 1}
        }
    }

    pokemon, trainers, energies, count = load_card_database(
        filename="tests/src/test_legal_cards.json"
    )
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies,
        "count": count
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid
    assert error == ""


def test_get_offset():
    assert get_offset("pokemon", 14) == 19
    assert get_offset("pokemon", 13) == 23
    assert get_offset("pokemon", 10) == 27
    assert get_offset("trainer", 20) == 23
    assert get_offset("trainer", 19) == 27
    assert get_offset("energy", 1) == 27
    assert get_offset("energy", 100) == 27


def test_fill_sheet_not_png():
    try:
        fill_sheet("bogus.jpg")
    except ValueError as e:
        assert str(e) == "Sheet location must be a PNG file."


@patch("src.core.Image")
@patch("src.core.ImageFont")
@patch("src.core.ImageDraw")
def test_fill_sheet_no_data(mock_draw, mock_font, mock_image):
    draw_instance = MagicMock()
    image_instance = MagicMock()
    mock_draw.Draw.return_value = draw_instance
    mock_image.open.return_value = image_instance

    fill_sheet()

    assert draw_instance.text.call_count == 2
    mock_image.open.assert_called_once()
    image_instance.save.assert_called_once()


@patch("src.core.Image")
@patch("src.core.ImageFont")
@patch("src.core.ImageDraw")
def test_fill_sheet(mock_draw, mock_font, mock_image):
    draw_instance = MagicMock()
    image_instance = MagicMock()
    mock_draw.Draw.return_value = draw_instance
    mock_image.open.return_value = image_instance

    fill_sheet(
        player={"name": "test boy"},
        cards={
            "pokemon": [{}],
            "trainers": {
                "test trainer": {}
            },
            "energies": {
                "test energy": {}
            }
        }
    )

    assert draw_instance.text.call_count == 11
    mock_image.open.assert_called_once()
    image_instance.save.assert_called_once()


def test_convert_banned_cards():
    banned_cards = {
        "standard": [
            ("Sewaddle", "white", "087"),
            ("Tool Scrapper", "white", "085"),
            ("Prism Energy", "black", "086"),
            ("Prism Energy Promo", "black promo", "086"),
        ]
    }

    sets = {
        "white": "WHT",
        "black": "BLK",
        "black promos": "BLK-PROMO"
    }

    with open("tests/src/test_legal_cards.json", "r") as f:
        legal_cards = json.load(f)

    result = convert_banned_cards(
        banned_cards, sets, legal_cards["cards"]
    )
    assert result["standard"]["pokemon"] == {
        "WHT": ["087"]
    }
    assert result["standard"]["trainers"] == [
        "Tool Scrapper"
    ]
    assert result["standard"]["energies"] == [
        "Prism Energy", "Prism Energy Promo"
    ]

    error = None
    try:
        convert_banned_cards(
            banned_cards, sets, {}
        )
    except Exception as e:
        error = e

    assert str(error) == (
        "Set code WHT not found in expanded cards."
    )

    error = None
    try:
        convert_banned_cards(
            banned_cards, sets, {"WHT": {}}
        )
    except Exception as e:
        error = e

    assert str(error) == (
        "Card number WHT-087 "
        "not found in expanded cards."
    )

    error = None
    try:
        convert_banned_cards(
            banned_cards, sets, {"WHT": {"087": {
                "type": "dunno"
            }}}
        )
    except Exception as e:
        error = e

    assert str(error) == (
        "Card WHT-087 "
        "has unknown type dunno."
    )
