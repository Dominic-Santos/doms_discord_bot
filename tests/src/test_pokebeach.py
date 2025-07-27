from unittest.mock import patch, MagicMock
from src.pokebeach import get_newsfeed

@patch('src.pokebeach.SB')
def test_get_newsfeed(mock_sb):
    mock_sb_instance = mock_sb.return_value
    
    post_1 = MagicMock()
    post_1.children = [post_1]
    post_1.__getitem__.side_effect = lambda key: "https://www.pokebeach.com/post1" if key == "href" else None

    post_2 = MagicMock()
    post_2.children = []

    mock_elements = MagicMock()
    mock_sb_instance.cdp.find_visible_elements.return_value = [mock_elements]
    mock_elements.children = [post_1, post_2]
    
    posts = get_newsfeed()

    assert len(posts) == 1
    assert posts[0] == "https://www.pokebeach.com/post1"
    mock_sb_instance.cdp.find_visible_elements.assert_called_once()
    mock_sb_instance.activate_cdp_mode.assert_called_once_with("https://www.pokebeach.com/")
    mock_sb_instance.sleep.assert_called_once_with(1)
