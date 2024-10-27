from datetime import datetime
from email.message import EmailMessage
from unittest.mock import MagicMock, call

from doveseed.domain_types import Email, FeedItem, State
from doveseed.email_notification import EmailNotifier
from doveseed.registration import Registration


def test_email_notifier():
    subscribers = [
        Registration(
            email=Email("mail1@test.org"),
            last_update=datetime.utcnow(),
            state=State.subscribed,
        ),
        Registration(
            email=Email("mail2@test.org"),
            last_update=datetime.utcnow(),
            state=State.subscribed,
        ),
    ]
    message = EmailMessage()
    feed_item = FeedItem(
        title="title",
        link="link",
        pub_date=datetime.now(),
        description="description",
        image=None,
    )

    storage = MagicMock()
    connection_manager = MagicMock()
    connection = MagicMock()
    message_provider = MagicMock()

    storage.get_all_active_subscribers.return_value = subscribers
    connection_manager.__enter__.return_value = connection
    message_provider.get_new_post_msg.return_value = message

    email_notifier = EmailNotifier(
        storage, lambda: connection_manager, message_provider
    )
    email_notifier(feed_item)

    message_provider.get_new_post_msg.assert_has_calls(
        (
            call(feed_item, Email("mail1@test.org")),
            call(feed_item, Email("mail2@test.org")),
        ),
        any_order=True,
    )
    connection.send_message.assert_has_calls((call(message), call(message)))
