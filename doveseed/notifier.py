from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from typing_extensions import Protocol


@dataclass
class FeedItem:
    title: str
    link: str
    pub_date: datetime
    description: str


class Storage(Protocol):
    def get_last_seen(self) -> datetime:
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
        self._storage.set_last_seen(max(item.pub_date for item in feed))
        for item in self._select_new_posts(feed, cutoff):
            self._consumer(item)

    def _select_new_posts(self, feed: Feed, cutoff: datetime):
        return (item for item in feed if item.pub_date > cutoff)
