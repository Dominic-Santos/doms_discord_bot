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