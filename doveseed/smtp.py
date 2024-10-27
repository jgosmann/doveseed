import ssl
from contextlib import contextmanager
from email.message import EmailMessage
from enum import Enum
from smtplib import SMTP, SMTP_SSL
from typing import Callable, ContextManager, Generator


class _EstablishedSmtpConnection:
    def __init__(self, smtp: SMTP):
        self._smtp = smtp

    def send_message(self, msg: EmailMessage) -> None:
        self._smtp.send_message(msg)


class _NoopConnection:
    def send_message(self, msg: EmailMessage) -> None:
        pass


ConnectionManager = Callable[[], ContextManager[_EstablishedSmtpConnection]]


class SslMode(Enum):
    NO_SSL = "no-ssl"
    START_TLS = "start-tls"
    TLS = "tls"

    @classmethod
    def from_str(cls, value: str) -> "SslMode":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError("not a valid SslMode")


@contextmanager
def _connect_smtp(
    host: str, port: int, *, context: ssl.SSLContext
) -> Generator[SMTP, None, None]:
    with SMTP(host, port) as smtp:
        if context is not None:
            smtp.starttls(context=context)
        yield smtp


def smtp_connection(
    *,
    host: str,
    user: str,
    password: str,
    port: int = 0,
    ssl_mode: str = SslMode.START_TLS.value,
    check_hostname: bool = True,
) -> ConnectionManager:
    _ssl_mode = SslMode.from_str(ssl_mode)
    context = None
    if _ssl_mode != SslMode.NO_SSL:
        context = ssl.create_default_context()
        context.check_hostname = check_hostname
    connect: Callable[..., ContextManager[SMTP]]
    if _ssl_mode == SslMode.TLS:
        connect = SMTP_SSL
    else:
        connect = _connect_smtp

    @contextmanager
    def connection_manager():
        with connect(host, port, context=context) as smtp:
            smtp.login(user, password)
            yield _EstablishedSmtpConnection(smtp)

    return connection_manager


def noop_connection() -> ConnectionManager:
    @contextmanager
    def connection_manager():
        yield _NoopConnection()

    return connection_manager
