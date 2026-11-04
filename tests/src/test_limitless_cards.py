import json
from unittest.mock import patch, mock_open, MagicMock

from src import limitless_cards as lc


def row(set_code, number, name, type_cell, rarity=""):
    return (
        '<tr data-hover="x">'
        f"<td>{set_code}</td>"
        f'<td><a href="/cards/{set_code}/{number}">{number}</a></td>'
        f"<td>{name}</td><td>{type_cell}</td><td>{rarity}</td><td>$1</td>"
        "</tr>"
    )


def page(rows, total=None, last_page=None):
    html = "".join(rows)
    if total is not None:
        html += f"<div>{total:,} cards found</div>"
    if last_page is not None:
        html += f'<ul data-max="{last_page}"></ul>'
    return html


PIKACHU = row("TWM", "128", "Pikachu&#039;s", '<span class="ptcg-symbol">L</span> Basic', "Common")
POTION = row("TWM", "150", "Potion", "Item", "Uncommon")
FIRE = row("TWM", "200", "Fire Energy", "Basic Energy")

SETS_PAGE = (
    '<td><a href="/cards/TWM"><img class="set" src="x"> Twilight Masquerade '
    '<span class="code annotation">TWM</span></a></td>'
    '<td><a href="/cards/PRE"><img class="set" src="x"> Prismatic Evolutions '
    '<span class="code annotation">PRE</span></a></td>'
)


def test_fetch_html():
    response = MagicMock()
    response.read.return_value = "hello".encode("utf-8")
    response.__enter__.return_value = response
    with patch("urllib.request.urlopen", return_value=response) as urlopen:
        assert lc.fetch_html("https://x") == "hello"
    assert urlopen.call_args[0][0].full_url == "https://x"


def test_convert_card_type():
    assert lc.convert_card_type('<span class="ptcg-symbol">L</span> Basic') == ("Pkmn > Basic", "Lightning")
    assert lc.convert_card_type('<span class="ptcg-symbol">?</span> Stage 1') == ("Pkmn > Stage 1", "")
    assert lc.convert_card_type("Basic Energy") == ("Energy > Basic", "")
    assert lc.convert_card_type("Special Energy") == ("Energy > Special", "")
    assert lc.convert_card_type("Supporter") == ("Trainer > Supporter", "")


def test_parse_card_rows():
    cards = lc.parse_card_rows(PIKACHU + FIRE)
    assert cards[0] == {
        "set": "TWM", "number": "128", "name": "Pikachu's",
        "type": "Pkmn > Basic", "color": "Lightning", "rarity": "Common",
        "link": "https://limitlesstcg.com/cards/TWM/128",
    }
    assert cards[1]["type"] == "Energy > Basic"


def test_parse_card_rows_replaces_characters():
    cards = lc.parse_card_rows(row("TWM", "1", "Boss’s Orders", "Supporter"))
    assert cards[0]["name"] == "Boss's Orders"


def test_get_total_cards():
    assert lc.get_total_cards("1,234 cards found") == 1234
    assert lc.get_total_cards("1 card found") == 1
    assert lc.get_total_cards("nothing") == 0


def test_get_all_pages():
    pages = {
        "u1": page([PIKACHU], last_page=2),
        "u2": page([POTION]),
    }
    with patch.object(lc, "fetch_html", side_effect=lambda u: pages[u]), \
            patch("time.sleep") as sleep:
        cards, first = lc.get_all_pages("u{page}")
    assert [c["name"] for c in cards] == ["Pikachu's", "Potion"]
    assert first == pages["u1"]
    sleep.assert_called_once()


def test_get_all_pages_single_page():
    with patch.object(lc, "fetch_html", return_value=page([PIKACHU])) as fetch:
        cards, _ = lc.get_all_pages("u{page}")
    assert len(cards) == 1
    fetch.assert_called_once()


def test_group_cards():
    grouped = lc.group_cards(lc.parse_card_rows(PIKACHU + POTION))
    assert grouped["TWM"]["128"]["name"] == "Pikachu's"
    assert "set" not in grouped["TWM"]["128"]
    assert "number" not in grouped["TWM"]["150"]


def test_get_set_list():
    with patch.object(lc, "fetch_html", return_value=SETS_PAGE):
        assert lc.get_set_list() == {
            "TWM": "Twilight Masquerade", "PRE": "Prismatic Evolutions"
        }


def test_get_legal_card_list():
    ace = row("TWM", "150", "Potion", "Item")

    def fetch(url):
        if "ace-spec" in url:
            return page([ace])
        return page([PIKACHU, POTION], total=2)

    with patch.object(lc, "fetch_html", side_effect=fetch), patch("time.sleep"):
        cards, total = lc.get_legal_card_list("standard", 0)
    assert total == 2
    assert cards["TWM"]["150"]["ace_spec"] is True
    assert "ace_spec" not in cards["TWM"]["128"]


def test_get_legal_card_list_up_to_date():
    with patch.object(lc, "fetch_html", return_value=page([PIKACHU], total=1)):
        assert lc.get_legal_card_list("standard", 1) == ({}, 1)


def test_get_legal_card_list_empty():
    with patch.object(lc, "fetch_html", return_value="no results"):
        assert lc.get_legal_card_list("standard", 5) == ({}, 0)


def test_get_legal_cards():
    results = [({"TWM": {}}, 3), ({}, 5)]
    m = mock_open()
    with patch.object(lc, "get_legal_card_list", side_effect=results) as get, \
            patch("builtins.open", m), patch("json.dump") as dump:
        lc.get_legal_cards("std.json", "exp.json", 1, 2)
    assert get.call_args_list[0][0] == ("standard", 1)
    assert get.call_args_list[1][0] == ("expanded", 2)
    m.assert_called_once_with("std.json", "w")
    assert dump.call_args[0][0] == {"cards": {"TWM": {}}, "count": 3}


def test_get_pokemon_sets():
    m = mock_open()
    with patch.object(lc, "get_set_list", return_value={"TWM": "Twilight Masquerade"}), \
            patch("builtins.open", m), patch("json.dump") as dump:
        lc.get_pokemon_sets("sets.json")
    m.assert_called_once_with("sets.json", "w")
    assert dump.call_args[0][0] == {
        "black star promo": "SMP", "twilight masquerade": "TWM"
    }


def test_get_all_cards():
    existing = json.dumps({"cards": {"OLD": {"1": {}}}})
    m = mock_open(read_data=existing)
    with patch.object(lc, "get_set_list", return_value={"TWM": "x"}), \
            patch.object(lc, "fetch_html", return_value=page([PIKACHU])), \
            patch("time.sleep"), patch("builtins.open", m), \
            patch("json.dump") as dump:
        lc.get_all_cards("db.json")
    saved = dump.call_args[0][0]["cards"]
    assert saved["OLD"] == {"1": {}}
    assert saved["TWM"]["128"]["name"] == "Pikachu's"


def test_get_all_cards_without_existing_file():
    m = mock_open()
    m.side_effect = [FileNotFoundError, mock_open().return_value]
    with patch.object(lc, "get_set_list", return_value={"TWM": "x"}), \
            patch.object(lc, "fetch_html", return_value="nothing"), \
            patch("time.sleep"), patch("builtins.open", m), \
            patch("json.dump") as dump:
        lc.get_all_cards("db.json")
    assert dump.call_args[0][0] == {"cards": {"TWM": {}}}
