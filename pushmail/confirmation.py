from base64 import b64encode
from email.message import EmailMessage
import html
import json
import os
import os.path
from urllib.parse import quote
from typing import Any, Callable, ContextManager, Dict

from jinja2 import Environment, FileSystemLoader, Template

from .smtp import ConnectionManager
from .registration import EMail, Action, Token


class EmailConfirmationRequester:
    def __init__(self, connection: ConnectionManager, template_path: str):
        self._connection = connection
        self._template_path = template_path
        self._template_env = Environment(loader=FileSystemLoader(self._template_path))
        self._template_env.filters["b64encode"] = lambda x: b64encode(x).decode("ascii")
        self._template_env.filters["utf8decode"] = lambda x: x.decode("utf-8")

    def request_confirmation(
        self, email: EMail, *, action: Action, confirm_token: Token
    ) -> None:

        encoded_token = b64encode(confirm_token).decode("ascii")
        confirm_link = "https://xyz.de/?token={token}".format(token=encoded_token)

        filelist = os.listdir(os.path.join(self._template_path, "files"))
        files = {filename: self._read_template_file(filename) for filename in filelist}

        env = dict(
            confirm_link=confirm_link,
            display_name="adventures.jgosmann.de",
            host="adventures.jgosmann.de",
            files=files,
        )

        subject = self._get_template(action, "subject.txt").render(**env)
        env["subject"] = subject

        plain_text = self._get_template(action, "txt").render(**env)
        html = self._get_template(action, "html").render(**env)

        msg = EmailMessage()
        msg.set_content(plain_text)
        msg.add_alternative(html, subtype="html")
        msg["Subject"] = subject
        msg["From"] = "Jan's outdoor adventures <adventures@jgosmann.de>"
        msg["To"] = email

        with self._connection() as connection:
            connection.send_message(msg)

    def _get_template(self, action: Action, template: str) -> Template:
        return self._template_env.get_template(f"{action.name}.{template}")

    def _read_template_file(self, filename: str) -> bytes:
        with open(os.path.join(self._template_path, "files", filename), "rb") as f:
            return f.read()
