from base64 import b64encode
from email.message import EmailMessage
import os.path

from jinja2 import Environment

from .registration import Action, EMail, Token


class FileSystemBinaryLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self, filename):
        with open(os.path.join(self.path, filename), "rb") as f:
            return f.read()


class EmailFromTemplateProvider:
    def __init__(self, template_loader, binary_loader):
        self._env = Environment(loader=template_loader)
        self._env.filters["b64encode"] = lambda x: b64encode(x).decode("ascii")
        self._env.filters["utf8decode"] = lambda x: x.decode("utf-8")
        self._env.globals["include_binary"] = binary_loader.load

    def get_confirmation_request_msg(
        self, to_email: EMail, *, action: Action, confirm_token: Token
    ) -> EmailMessage:
        encoded_token = b64encode(confirm_token).decode("ascii")
        confirm_link = "https://xyz.de/?token={token}".format(token=encoded_token)

        substitutions = dict(
            confirm_link=confirm_link,
            display_name="adventures.jgosmann.de",
            host="adventures.jgosmann.de",
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
        msg["From"] = "Jan's outdoor adventures <adventures@jgosmann.de>"
        msg["To"] = to_email

        return msg
