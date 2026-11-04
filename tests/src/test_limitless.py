import pytest

from src.limitless import (
    parse_decklist_url, build_card_lookup, get_decklist_from_url
)

EXAMPLE = (
    "my.limitlesstcg.com/builder?i=10433TWM1280433TWM1290333TWM1300232TWM95"
    "0232ASC160133TEF1280133TEF1290132POR620133ASC1420433MEG1190333MEG114"
    "0233SCR1330132POR840132POR760433TEF1440432POR810432POR710333MEG131"
    "0333ASC1960133TWM1650233MEG1270332MEE100332MEE130332MEE15"
)


def test_parse_decklist_url():
    cards = parse_decklist_url("https://" + EXAMPLE)
    assert cards[0] == (4, "TWM", "128")
    assert cards[3] == (2, "TWM", "95")
    assert cards[-3:] == [(3, "MEE", "10"), (3, "MEE", "13"), (3, "MEE", "15")]
    assert len(cards) == 24
    assert sum(c[0] for c in cards) == 60
    assert parse_decklist_url("HTTP://" + EXAMPLE) == cards
    assert parse_decklist_url(EXAMPLE) == cards


def test_parse_quantities_and_trailing_zero_numbers():
    assert parse_decklist_url("x/builder?i=10a33TWM1000Z32MEE7") == [
        (10, "TWM", "100"), (61, "MEE", "7")
    ]
    assert parse_decklist_url("x/builder?i=10133TWM100") == [
        (1, "TWM", "100")
    ]


@pytest.mark.parametrize("url", [
    "x/builder?i=10_33TWM1",
    "x/builder?i=1033TWM",
    "x/builder?i=1033TWM1X",
    "x/builder?i=0433TWM1",
    "x/other?i=10433TWM1",
])
def test_parse_invalid(url):
    with pytest.raises(ValueError):
        parse_decklist_url(url)


def test_get_decklist_from_url():
    lookup = build_card_lookup({"cards": {
        "TWM": {"128": {"name": "Pikachu", "type": "Pkmn Basic"}},
        "MEE": {"007": {"name": "Fire Energy", "type": "Energy Basic"}},
        "ASC": {"16": {"name": "Potion", "type": "Trainer Item"}},
    }})
    deck = get_decklist_from_url(
        "x/builder?i=10433TWM1280232ASC16 0332MEE7".replace(" ", ""), lookup
    )
    assert deck["pokemon"] == [
        {"quantity": 4, "name": "Pikachu", "set": "TWM", "number": 128}
    ]
    assert deck["trainers"] == {"Potion": {"quantity": 2}}
    assert deck["energies"] == {"Fire Energy": {"quantity": 3}}

    with pytest.raises(ValueError):
        get_decklist_from_url("x/builder?i=10433TWM1", lookup)
