from datetime import datetime, timedelta, tzinfo
from xml.etree import ElementTree

from doveseed.domain_types import FeedItem
from doveseed.feed import parse_rss


sample_rss = ElementTree.fromstring(
    """
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:og="http://ogp.me/ns#">
  <channel>
    <title>title</title>
    <link>https://link.org/</link>
    <description>description</description>
    <generator>generator</generator>
    <language>en-us</language>
    <lastBuildDate>Thu, 03 Oct 2019 20:11:47 +0200</lastBuildDate>
    <atom:link href="https://link.org/index.xml" rel="self" type="application/rss+xml" />
    <item>
      <title>Item title</title>
      <link>https://link.org/post/</link>
      <pubDate>Thu, 03 Oct 2019 20:11:47 GMT</pubDate>
      <guid>https://link.org/post/</guid>
      <description>description</description>
      <og:image>image</og:image>
    </item>
  </channel>
</rss>
"""
)


class TimezoneOffset(tzinfo):
    def __init__(self, offset):
        self._offset = offset

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return f"{self._offset.hours:02}{self._offset.minutes:02}"


def test_parse_rss():
    parsed = list(parse_rss(sample_rss))
    assert parsed == [
        FeedItem(
            title="Item title",
            link="https://link.org/post/",
            pub_date=datetime(2019, 10, 3, 20, 11, 47),
            description="description",
            image="image",
        )
    ]
