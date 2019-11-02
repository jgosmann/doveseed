from base64 import b64encode
from dataclasses import dataclass
from email.message import EmailMessage
import os.path
from urllib.parse import quote

from jinja2 import Environment

from .registration import Action, EMail, Token


class FileSystemBinaryLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self, filename):
        with open(os.path.join(self.path, filename), "rb") as f:
            return f.read()


class EmailFromTemplateProvider:
    @dataclass
    class Settings:
        display_name: str
        sender: str
        host: str
        confirm_url_format: str

    def __init__(self, *, settings: Settings, template_loader, binary_loader):
        self.settings = settings
        self._env = Environment(loader=template_loader)
        self._env.filters["b64encode"] = lambda x: b64encode(x).decode("ascii")
        self._env.globals["include_binary"] = binary_loader.load

    def get_confirmation_request_msg(
        self, to_email: EMail, *, action: Action, confirm_token: Token
    ) -> EmailMessage:
        encoded_token = quote(b64encode(confirm_token).decode("ascii"))
        confirm_link = self.settings.confirm_url_format.format(
            email=to_email, host=self.settings.host, token=encoded_token
        )

        substitutions = dict(
            confirm_link=confirm_link,
            display_name=self.settings.display_name,
            host=self.settings.host,
            to_email=to_email,
        )

        subject = self._env.get_template(f"{action.name}.subject.txt").render(
            **substitutions
        )
        substitutions["subject"] = subject

        plain_text = self._env.get_template(f"{action.name}.txt").render(
            **substitutions
        )
        html = self._env.get_template(f"{action.name}.html").render(**substitutions)

        msg = EmailMessage()
        msg.set_content(plain_text)
        msg.add_alternative(html, subtype="html")
        msg["Subject"] = subject
        msg["From"] = self.settings.sender
        msg["To"] = to_email

        return msg
