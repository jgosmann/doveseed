from contextlib import contextmanager
from email.message import EmailMessage
from smtplib import SMTP
import ssl
from typing import Callable, ContextManager


class _EstablishedSmtpConnection:
    def __init__(self, smtp: SMTP):
        self._smtp = smtp

    def send_message(self, msg: EmailMessage) -> None:
        self._smtp.send_message(msg)


class _NoopConnection:
    def send_message(self, msg: EmailMessage) -> None:
        pass


ConnectionManager = Callable[[], ContextManager[_EstablishedSmtpConnection]]


def smtp_connection(host: str, user: str, password: str) -> ConnectionManager:
    context = ssl.create_default_context()
    context.check_hostname = True

    @contextmanager
    def connection_manager():
        with SMTP(host) as smtp:
            smtp.starttls(context=context)
            smtp.login(user, password)
            yield _EstablishedSmtpConnection(smtp)

    return connection_manager


def noop_connection() -> ConnectionManager:
    @contextmanager
    def connection_manager():
        yield _NoopConnection()

    return connection_manager
