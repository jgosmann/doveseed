from email.message import EmailMessage
from typing import Iterable

from typing_extensions import Protocol

from .domain_types import Email, FeedItem
from .registration import Registration
from .smtp import ConnectionManager


class Storage(Protocol):
    def get_all_active_subscribers(self) -> Iterable[Registration]:
        ...


class EmailMessageProvider(Protocol):
    def get_new_post_msg(self, feed_item: FeedItem, to_email: Email) -> EmailMessage:
        ...


class EmailNotifier:
    def __init__(
        self,
        storage: Storage,
        connection: ConnectionManager,
        message_provider: EmailMessageProvider,
    ):
        self._subscribers = list(storage.get_all_active_subscribers())
        self._connection = connection
        self._message_provider = message_provider

    def __call__(self, feed_item: FeedItem):
        with self._connection() as connection:
            for subscriber in self._subscribers:
                message = self._message_provider.get_new_post_msg(
                    feed_item, subscriber.email
                )
                connection.send_message(message)
