from contextlib import contextmanager
from email.message import EmailMessage
from smtplib import SMTP
from typing import Callable, ContextManager


class _EstablishedSmtpConnection:
    def __init__(self, smtp: SMTP):
        self._smtp = smtp

    def send_message(self, msg: EmailMessage) -> None:
        self._smtp.send_message(msg)


ConnectionManager = Callable[[], ContextManager[_EstablishedSmtpConnection]]


def smtp_connection(host: str, user: str, password: str) -> ConnectionManager:
    @contextmanager
    def connection_manager():
        with SMTP(host) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            yield _EstablishedSmtpConnection(smtp)

    return connection_manager
