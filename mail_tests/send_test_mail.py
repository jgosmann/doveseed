#!/usr/bin/env python

import argparse
from email.message import EmailMessage
import getpass
import sys

from jinja2 import FileSystemLoader

from pushmail.smtp import smtp_connection
from pushmail.email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader
from pushmail.registration import Action, EMail, Token


parser = argparse.ArgumentParser(
    description="Generate and send test emails from a template."
)
parser.add_argument(
    "--host", "-H", type=str, nargs=1, help="SMTP host to connect to.", required=True
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
    choices=("subscribe", "unsubscribe"),
    nargs="+",
    help="Types of emails to send.",
    default=("subscribe", "unsubscribe"),
)

if __name__ == "__main__":
    args = parser.parse_args()

    user = args.user if args.user else args.from_mail[0]

    conn = smtp_connection(args.host[0], user, getpass.getpass(f"Password for {user}:"))

    settings = EmailFromTemplateProvider.Settings(
        display_name="Pushmail template test",
        sender=args.from_mail[0],
        host="pushmail.local",
        confirm_url_format="https://{host}/confirm/{email}?token={token}",
    )
    message_provider = EmailFromTemplateProvider(
        settings=settings,
        template_loader=FileSystemLoader(args.template[0]),
        binary_loader=FileSystemBinaryLoader(args.template[0]),
    )

    token = Token(b"token")
    dispatch = dict(
        subscribe=lambda: message_provider.get_confirmation_request_msg(
            args.to_mail[0], action=Action.subscribe, confirm_token=token
        ),
        unsubscribe=lambda: message_provider.get_confirmation_request_msg(
            args.to_mail[0], action=Action.unsubscribe, confirm_token=token
        ),
    )

    with conn() as smtp:
        for email_type in args.types:
            smtp.send_message(dispatch[email_type]())
