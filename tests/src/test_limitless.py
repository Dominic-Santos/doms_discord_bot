from unittest.mock import patch, MagicMock
from src.limitless import get_decklist_from_url


@patch('src.limitless.Driver')
def test_get_decklist_from_url(mock_driver):
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    table_mock = MagicMock()
    mock_driver_instance.cdp.find_visible_elements.return_value = [
        table_mock, table_mock, table_mock, table_mock, table_mock
    ]

    table_children = [
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="th", text="Pokemon"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="td", text="1"),
            MagicMock(tag_name="td", text="Pikachu"),
            MagicMock(tag_name="td", text="Base Set"),
            MagicMock(tag_name="td", text="25"),
            MagicMock(tag_name="td", text="H"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="th", text="Trainer"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="td", text="2"),
            MagicMock(tag_name="td", text="Potion"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="th", text="Energy"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="td", text="3"),
            MagicMock(tag_name="td", text="Fire Energy"),
        ]),
        MagicMock(tag_name="tr", children=[
            MagicMock(tag_name="td", text="3"),
        ]),
    ]
    table_mock.children = table_children

    result = get_decklist_from_url("https://example.com/decklist")

    assert mock_driver_instance.uc_activate_cdp_mode.call_count == 1
    assert mock_driver_instance.sleep.call_count == 3
    assert mock_driver_instance.cdp.find_visible_elements.call_count == 3
    assert mock_driver_instance.quit.call_count == 1
    assert len(result["pokemon"]) == 1
    assert result["pokemon"][0]["name"] == "Pikachu"
    assert len(result["trainers"]) == 1
    assert result["trainers"]["Potion"]["quantity"] == 2
    assert len(result["energies"]) == 1
    assert result["energies"]["Fire Energy"]["quantity"] == 3
