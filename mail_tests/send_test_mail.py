#!/usr/bin/env python

import argparse
import getpass
from datetime import datetime

from jinja2 import FileSystemLoader

from doveseed.domain_types import Action, FeedItem, Token
from doveseed.email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader
from doveseed.smtp import SslMode, smtp_connection

LoremIpsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. In
dictum commodo odio, sed blandit dui convallis eget. Donec quis ipsum urna.
Aenean a dolor eget nibh tincidunt porta vitae id dui. Morbi vitae sapien erat.
Mauris et mollis risus, et feugiat libero. Pellentesque quis scelerisque erat.
Fusce sollicitudin aliquam orci vitae tristique. Donec vulputate dolor ut
malesuada molestie. Nunc tempus tellus vel ipsum aliquam, ac tincidunt metus
aliquet. Curabitur non molestie nunc."""

parser = argparse.ArgumentParser(
    description="Generate and send test emails from a template."
)
parser.add_argument(
    "--host", "-H", type=str, nargs=1, help="SMTP host to connect to.", required=True
)
parser.add_argument(
    "--port",
    "-p",
    type=int,
    nargs=1,
    help="SMTP port to connect to.",
    required=False,
    default=[0],
)
parser.add_argument(
    "--ssl",
    type=str,
    nargs=1,
    help="SMTP SSL mode.",
    required=False,
    default=[SslMode.START_TLS.value],
    choices=[mode.value for mode in SslMode],
)
parser.add_argument(
    "--user",
    "-u",
    type=str,
    nargs="?",
    help="User name to connect to SMTP host, defaults to 'from'.",
)
parser.add_argument(
    "--from",
    "-f",
    type=str,
    nargs=1,
    dest="from_mail",
    help="From field of email to be sent.",
    required=True,
)
parser.add_argument(
    "--to",
    "-t",
    type=str,
    nargs=1,
    dest="to_mail",
    help="To field of email to be sent.",
    required=True,
)
parser.add_argument(
    "--template", "-T", type=str, nargs=1, help="Path to the template.", required=True
)
parser.add_argument(
    "--types",
    type=str,
    choices=("subscribe", "unsubscribe", "new-post"),
    nargs="+",
    help="Types of emails to send.",
    default=("subscribe", "unsubscribe", "new-post"),
)
parser.add_argument(
    "--image",
    type=str,
    nargs=1,
    help="Image to use for new-post email.",
    default=[None],
)

if __name__ == "__main__":
    args = parser.parse_args()

    user = args.user if args.user else args.from_mail[0]

    conn = smtp_connection(
        host=args.host[0],
        user=user,
        password=getpass.getpass(f"Password for {user}:"),
        port=args.port[0],
        ssl_mode=args.ssl[0],
    )

    settings = EmailFromTemplateProvider.Settings(
        display_name="Doveseed template test",
        sender=args.from_mail[0],
        host="doveseed.local",
        confirm_url_format="https://{host}/confirm/{email}?token={token}",
    )
    message_provider = EmailFromTemplateProvider(
        settings=settings,
        template_loader=FileSystemLoader(args.template[0]),
        binary_loader=FileSystemBinaryLoader(args.template[0]),
    )

    token = Token(b"token")
    dispatch = {
        "subscribe": lambda: message_provider.get_confirmation_request_msg(
            args.to_mail[0], action=Action.subscribe, confirm_token=token
        ),
        "unsubscribe": lambda: message_provider.get_confirmation_request_msg(
            args.to_mail[0], action=Action.unsubscribe, confirm_token=token
        ),
        "new-post": lambda: message_provider.get_new_post_msg(
            FeedItem(
                title="Post title",
                description=LoremIpsum,
                link="https://doveseed.local/post",
                pub_date=datetime.now(),
                image=args.image[0],
            ),
            args.to_mail[0],
        ),
    }

    with conn() as smtp:
        for email_type in args.types:
            smtp.send_message(dispatch[email_type]())
