from datetime import datetime, timedelta
import json
from typing import Any, Dict

from jinja2 import FileSystemLoader
from tinydb import TinyDB

from .email_notification import EmailNotifier
from .email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader
from .feed import get_feed, parse_rss
from .notifier import NewPostNotifier
from .smtp import smtp_connection
from .storage import TinyDbStorage


def clean_unconfirmed(config: Dict[str, Any]) -> None:
    db = TinyDB(config["db"])
    storage = TinyDbStorage(db)
    storage.drop_old_unconfirmed(
        drop_before=datetime.utcnow()
        - timedelta(minutes=config["confirm_timeout_minutes"])
    )


def notify_subscribers(config: Dict[str, Any]) -> None:
    db = TinyDB(config["db"])
    storage = TinyDbStorage(db)
    connection = smtp_connection(**config["smtp"])
    message_provider = EmailFromTemplateProvider(
        settings=EmailFromTemplateProvider.Settings(**config["template_vars"]),
        template_loader=FileSystemLoader(config["email_templates"]),
        binary_loader=FileSystemBinaryLoader(config["email_templates"]),
    )
    email_notifier = EmailNotifier(storage, connection, message_provider)
    feed_consumer = NewPostNotifier(storage, email_notifier)
    feed_consumer(parse_rss(get_feed(config["rss"])))


Actions = {"clean": clean_unconfirmed, "notify": notify_subscribers}


if __name__ == "__main__":
    import argparse
    import os
    import os.path

    parser = argparse.ArgumentParser(description="Triggers a doveseed action")
    parser.add_argument(
        "action",
        type=str,
        nargs=1,
        choices=("clean", "notify"),
        help="Action to perform: 'clean' to clean expired pending subscriptions; 'notify' to notify active subscribers about new posts.",
    )
    parser.add_argument(
        "config", type=str, nargs=1, help="configuration file", metavar="config"
    )

    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(args.config[0])))
    with open(args.config[0], "r") as f:
        config = json.load(f)

    Actions[args.action[0]](config)
