from email.message import EmailMessage

from typing_extensions import Protocol

from .domain_types import Action, Email, Token
from .smtp import ConnectionManager


class EmailMessageProvider(Protocol):
    def get_confirmation_request_msg(
        self, to_email: Email, *, action: Action, confirm_token: Token
    ) -> EmailMessage: ...


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
