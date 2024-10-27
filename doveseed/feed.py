import urllib.request
from email.utils import parsedate_to_datetime
from typing import Iterable
from xml.etree import ElementTree

from .domain_types import FeedItem


def get_feed(url: str) -> ElementTree.Element:
    with urllib.request.urlopen(url) as response:
        return ElementTree.fromstringlist(response)


def parse_rss(rss: ElementTree.Element) -> Iterable[FeedItem]:
    channel = rss.find("channel")
    if channel is None:
        return
    for item in channel.findall("item"):
        try:
            yield FeedItem(
                title=_get_optional(item, "title", ""),
                link=_get_required(item, "link"),
                pub_date=parsedate_to_datetime(_get_required(item, "pubDate")),
                description=_get_optional(item, "description", ""),
                image=_get_optional(item, "og:image"),
            )
        except RequiredElementError:
            pass


_ns = {"og": "http://ogp.me/ns#"}


def _get_optional(item, tag, default=None):
    elem = item.find(tag, _ns)
    if elem is None:
        return default
    return elem.text


def _get_required(item, tag):
    elem = item.find(tag, _ns)
    if elem is None:
        raise RequiredElementError(tag)
    return elem.text


class RequiredElementError(LookupError):
    pass
