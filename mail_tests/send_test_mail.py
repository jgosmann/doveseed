#!/usr/bin/env python

import getpass

from jinja2 import FileSystemLoader

from pushmail.confirmation import EmailConfirmationRequester
from pushmail.registration import Action, EMail, Token
from pushmail.smtp import smtp_connection
from pushmail.email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader


if __name__ == "__main__":
    conn = smtp_connection(
        "v22013121181015858.yourvserver.net",
        "adventures@jgosmann.de",
        getpass.getpass("smtp pass:"),
    )
    template_path = "templates/adventures"
    message_provider = EmailFromTemplateProvider(
        FileSystemLoader(template_path), FileSystemBinaryLoader(template_path)
    )
    confirmation_requester = EmailConfirmationRequester(conn, message_provider)
    confirmation_requester.request_confirmation(
        EMail("jan@hyper-world.de"),
        action=Action.subscribe,
        confirm_token=Token(b"uiea"),
    )
