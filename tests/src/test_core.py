from unittest.mock import patch, MagicMock
from src.core import validate_decklist, fill_sheet, load_card_database

def test_load_card_database_not_json():
    try:
        load_card_database("tests/data/invalid_format.txt")
    except ValueError as e:
        assert str(e) == "Filename must be a JSON file."

@patch("builtins.open")
def test_load_card_database_invalid_json(mock_open):
    mock_open.side_effect = [MagicMock(read=MagicMock(return_value="invalid json"))]
    try:
        load_card_database("tests/data/invalid_format.json")
    except ValueError as e:
        assert str(e) == "Error loading JSON file."

def test_load_card_database():
    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")
    all_pokemon = [p for set in pokemon for p in pokemon[set]]
    assert len(all_pokemon) == 323
    assert len(trainers.keys()) == 14
    assert len(energies.keys()) == 2

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

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")

    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
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

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")

    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
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

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
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

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
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

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid is False
    assert error == "Energy card fake energy is not legal."

def test_validate_decklist():
    decklist = {
        "pokemon": [
            {"name": "Sewaddle", "quantity": 1, "set": "WHT", "number": "87"}
        ],
        "energies": {
            "fire energy": {"quantity": 59},
        },
        "trainers": {
        }
    }

    pokemon, trainers, energies = load_card_database(filename="tests/src/test_legal_cards.json")
    legalcards = {
        "pokemon": pokemon,
        "trainers": trainers,
        "energies": energies
    }
    valid, error = validate_decklist(decklist, legal_cards=legalcards)
    assert valid
    assert error == ""