from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from doveseed.notifier import FeedItem, NewPostNotifier


ReferenceDatetime = datetime(2019, 11, 22)

OldFeedItem = FeedItem(
    title="Old item",
    link="old link",
    pub_date=ReferenceDatetime - timedelta(days=1),
    description="old description",
)
NewFeedItem = FeedItem(
    title="New item",
    link="new link",
    pub_date=ReferenceDatetime + timedelta(days=1),
    description="new description",
)


class InMemoryStorage:
    def __init__(self):
        self.last_seen = ReferenceDatetime

    def get_last_seen(self) -> datetime:
        return self.last_seen

    def set_last_seen(self, value: datetime) -> None:
        self.last_seen = value


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def consumer():
    return MagicMock()


@pytest.fixture
def new_post_notifier(storage, consumer):
    return NewPostNotifier(storage, consumer)


@pytest.fixture
def feed():
    return (OldFeedItem, NewFeedItem)


class TestNewPostNotifier:
    def test_stores_last_seen_date(self, storage, feed, new_post_notifier):
        new_post_notifier(feed)
        assert storage.get_last_seen() == NewFeedItem.pub_date

    def test_notifies_consumer_for_new_items(self, consumer, feed, new_post_notifier):
        new_post_notifier(feed)
        consumer.assert_called_once_with(NewFeedItem)
