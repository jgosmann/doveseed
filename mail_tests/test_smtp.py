#!/usr/bin/env python

import argparse
from email.message import EmailMessage
import getpass
import sys

from doveseed.smtp import smtp_connection


parser = argparse.ArgumentParser(
    description="Test the smtp module by sending a test email."
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

if __name__ == "__main__":
    args = parser.parse_args()

    user = args.user if args.user else args.from_mail[0]

    conn = smtp_connection(args.host[0], user, getpass.getpass(f"Password for {user}:"))

    msg = EmailMessage()
    msg["Subject"] = "Doveseed SMTP test mail"
    msg.set_content(f"This email was sent with: {' '.join(sys.argv)}")
    msg["From"] = args.from_mail[0]
    msg["To"] = args.to_mail[0]

    with conn() as smtp:
        smtp.send_message(msg)
