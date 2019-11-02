#!/usr/bin/env python

import getpass

from pushmail.confirmation import EmailConfirmationRequester
from pushmail.registration import Action, EMail, Token
from pushmail.smtp import smtp_connection


if __name__ == "__main__":
    conn = smtp_connection(
        "v22013121181015858.yourvserver.net",
        "adventures@jgosmann.de",
        getpass.getpass("smtp pass:"),
    )
    confirmation_requester = EmailConfirmationRequester(conn, "templates/adventures")
    confirmation_requester.request_confirmation(
        EMail("jan@hyper-world.de"),
        action=Action.subscribe,
        confirm_token=Token(b"uiea"),
    )
