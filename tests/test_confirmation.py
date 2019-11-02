from email.message import EmailMessage
from unittest.mock import MagicMock

from pushmail.confirmation import EmailConfirmationRequester
from pushmail.types import EMail, Token, Action


def test_email_confirmation_requester():
    email = EMail("email")
    action = Action.subscribe
    confirm_token = Token(b"token")
    message = EmailMessage()

    connection_manager = MagicMock()
    connection = MagicMock()
    message_provider = MagicMock()

    connection_manager.__enter__.return_value = connection
    message_provider.get_confirmation_request_msg.return_value = message

    requester = EmailConfirmationRequester(
        connection=lambda: connection_manager, message_provider=message_provider
    )
    requester.request_confirmation(email, action=action, confirm_token=confirm_token)

    message_provider.get_confirmation_request_msg.assert_called_once_with(
        email, action=action, confirm_token=confirm_token
    )
    connection.send_message.assert_called_once_with(message)
