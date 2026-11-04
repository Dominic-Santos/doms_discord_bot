from unittest.mock import patch, MagicMock
from src.pokebeach import get_newsfeed, NEWSFEED_URL

FEED = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel>
<link>https://www.pokebeach.com/forums/</link>
<item><title>One</title><link>https://www.pokebeach.com/forums/threads/one.1/</link></item>
<item><title>No link</title></item>
<item><title>Two</title><link> https://www.pokebeach.com/forums/threads/two.2/ </link></item>
</channel></rss>"""


@patch("urllib.request.urlopen")
def test_get_newsfeed(mock_urlopen):
    response = MagicMock()
    response.read.return_value = FEED.encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = response

    posts = get_newsfeed()

    assert posts == [
        "https://www.pokebeach.com/forums/threads/one.1/",
        "https://www.pokebeach.com/forums/threads/two.2/",
    ]
    assert mock_urlopen.call_args[0][0].full_url == NEWSFEED_URL
