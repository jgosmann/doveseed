from base64 import b64encode
from email.message import EmailMessage
import html
import json
import os
import os.path
from urllib.parse import quote
from typing import Any, Callable, ContextManager, Dict

from jinja2 import Environment, FileSystemLoader, Template
from typing_extensions import Protocol

from .smtp import ConnectionManager
from .domain_types import Email, Token, Action


class EmailMessageProvider(Protocol):
    def get_confirmation_request_msg(
        self, to_email: Email, *, action: Action, confirm_token: Token
    ) -> EmailMessage:
        ...


class EmailConfirmationRequester:
    def __init__(
        self, *, connection: ConnectionManager, message_provider: EmailMessageProvider
    ):
        self._connection = connection
        self._message_provider = message_provider

    def request_confirmation(
        self, email: Email, *, action: Action, confirm_token: Token
    ) -> None:
        message = self._message_provider.get_confirmation_request_msg(
            email, action=action, confirm_token=confirm_token
        )
        with self._connection() as connection:
            connection.send_message(message)
