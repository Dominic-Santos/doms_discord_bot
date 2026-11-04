import urllib.request
import xml.etree.ElementTree as ET

NEWSFEED_URL = "https://www.pokebeach.com/forums/forums/front-page-news.18/index.rss"
USER_AGENT = "Mozilla/5.0"
REQUEST_TIMEOUT = 60


def get_newsfeed() -> list[str]:
    request = urllib.request.Request(
        NEWSFEED_URL, headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        feed = ET.fromstring(response.read())

    return [
        link.strip()
        for item in feed.iter("item")
        if (link := item.findtext("link"))
    ]
