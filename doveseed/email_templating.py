import mimetypes
import os.path
from base64 import b64encode
from dataclasses import dataclass
from email.message import EmailMessage, Message, MIMEPart
from typing import List, Mapping, Optional, Tuple, cast
from urllib.parse import quote
from uuid import uuid1

from jinja2 import Environment

from .domain_types import Action, Email, FeedItem, Token


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
        self._binary_loader = binary_loader
        self._env = Environment(loader=template_loader)
        self._env.filters["b64encode"] = lambda x: b64encode(x).decode("ascii")
        self._env.filters["urlquote"] = quote
        self._env.globals["include_binary"] = binary_loader.load

    def get_confirmation_request_msg(
        self, to_email: Email, *, action: Action, confirm_token: Token
    ) -> EmailMessage:
        encoded_token = quote(confirm_token.to_string())
        confirm_link = self.settings.confirm_url_format.format(
            action=action.name,
            email=quote(to_email),
            host=self.settings.host,
            token=encoded_token,
        )

        substitutions = {
            "confirm_link": confirm_link,
            "display_name": self.settings.display_name,
            "host": self.settings.host,
            "to_email": to_email,
        }

        return self._msg_from_template(action.name, to_email, substitutions)

    def get_new_post_msg(self, feed_item: FeedItem, to_email: Email) -> EmailMessage:
        substitutions = dict(
            {
                "display_name": self.settings.display_name,
                "host": self.settings.host,
                "to_email": to_email,
                "post": feed_item,
            }
        )

        return self._msg_from_template("new-post", to_email, substitutions)

    def _msg_from_template(
        self, template: str, to_email: str, substitutions: Mapping[str, object]
    ) -> EmailMessage:
        substitutions = dict(substitutions)
        subject = self._env.get_template(f"{template}.subject.txt").render(
            **substitutions
        )
        substitutions["subject"] = subject

        plain_text_related_collector = _RelatedPartsCollector(self._binary_loader)
        plain_text = (
            plain_text_related_collector.overlay_env(self._env)
            .get_template(f"{template}.txt")
            .render(**substitutions)
        )
        html_related_collector = _RelatedPartsCollector(self._binary_loader)
        html = (
            html_related_collector.overlay_env(self._env)
            .get_template(f"{template}.html")
            .render(**substitutions)
        )

        msg = EmailMessage()
        msg.set_content(plain_text)
        msg.add_alternative(html, subtype="html")
        plain_text_related_collector.assemble(msg.get_body(("plain",)))
        html_related_collector.assemble(msg.get_body(("html",)))
        msg["Subject"] = subject
        msg["From"] = self.settings.sender
        msg["To"] = to_email

        return msg


@dataclass(frozen=True)
class RelatedPartInfo:
    content_id: str
    filename: str
    content_type: Tuple[str, str]
    path: str


class _RelatedPartsCollector:
    def __init__(self, binary_loader):
        self.parts: List[RelatedPartInfo] = []
        self.binary_loader = binary_loader

    def overlay_env(self, env: Environment):
        overlay_env = env.overlay()
        overlay_env.globals["include_related"] = self.include_related
        return overlay_env

    def include_related(
        self,
        path: str,
        *,
        filename: Optional[str] = None,
        content_type: Optional[Tuple[str, str]] = None,
    ) -> RelatedPartInfo:
        content_id = str(uuid1())

        if filename is None:
            filename = os.path.basename(path)

        if content_type is None:
            raw_content_type, _ = mimetypes.guess_type(path)
            content_type = cast(
                Tuple[str, str],
                tuple(
                    (raw_content_type or "application/octet-stream").split(
                        "/", maxsplit=1
                    )
                ),
            )

        part_info = RelatedPartInfo(
            content_id=content_id,
            filename=filename,
            content_type=content_type,
            path=path,
        )
        self.parts.append(part_info)
        return part_info

    def assemble(self, body: Optional[Message]) -> None:
        if not isinstance(body, MIMEPart):
            return
        for part in self.parts:
            body.add_related(
                self.binary_loader.load(part.path),
                maintype=part.content_type[0],
                subtype=part.content_type[1],
                cid=part.content_id,
                filename=part.filename,
                disposition="inline",
            )
