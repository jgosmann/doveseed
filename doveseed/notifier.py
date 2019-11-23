from datetime import datetime
from typing import Iterable, Optional

from typing_extensions import Protocol

from .domain_types import FeedItem


class Storage(Protocol):
    def get_last_seen(self) -> Optional[datetime]:
        ...

    def set_last_seen(self, value: datetime) -> None:
        ...


class Consumer(Protocol):
    def __call__(self, feed_item: FeedItem) -> None:
        ...


Feed = Iterable[FeedItem]


class NewPostNotifier:
    def __init__(self, storage: Storage, consumer: Consumer):
        self._storage = storage
        self._consumer = consumer

    def __call__(self, feed: Feed) -> None:
        cutoff = self._storage.get_last_seen()
        feed = list(feed)
        last_seen = (
            max(item.pub_date for item in feed) if len(feed) > 0 else datetime.utcnow()
        )
        self._storage.set_last_seen(last_seen)
        chronological = sorted(
            self._select_new_posts(feed, cutoff), key=lambda item: item.pub_date
        )
        for item in chronological:
            self._consumer(item)

    def _select_new_posts(self, feed: Feed, cutoff: Optional[datetime]):
        if cutoff is None:
            return feed
        return (item for item in feed if item.pub_date > cutoff)
