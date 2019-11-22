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
NewestFeedItem = FeedItem(
    title="Newest item",
    link="newest link",
    pub_date=ReferenceDatetime + timedelta(days=2),
    description="newest description",
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


class TestNewPostNotifier:
    def test_stores_last_seen_date(self, storage, new_post_notifier):
        new_post_notifier((OldFeedItem, NewestFeedItem))
        assert storage.get_last_seen() == NewestFeedItem.pub_date

    def test_notifies_consumer_for_new_items(self, consumer, new_post_notifier):
        new_post_notifier((OldFeedItem, NewestFeedItem))
        consumer.assert_called_once_with(NewestFeedItem)

    def test_notifies_in_chronological_order(self, consumer, new_post_notifier):
        new_post_notifier((NewestFeedItem, NewFeedItem))
        datetimes = [call[0][0].pub_date for call in consumer.call_args_list]
        assert sorted(datetimes) == datetimes
