from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Iterator, NewType, Optional

from typing_extensions import Protocol


EMail = NewType("EMail", str)
Token = NewType("Token", bytes)

State = Enum("State", ("pending_subscribe", "subscribed", "pending_unsubscribe"))
Action = Enum("Action", ("subscribe", "unsubscribe"))


@dataclass
class Registration:
    email: EMail
    last_update: datetime
    state: State
    confirm_token: Optional[Token] = None
    confirm_action: Optional[Action] = None
    immediate_unsubscribe_token: Optional[Token] = None


class Storage(Protocol):
    def upsert(self, registration: Registration) -> None:
        ...

    def find(self, email: EMail) -> Optional[Registration]:
        ...


class Mailer(Protocol):
    def mail_subscribe_confirm(self, email: EMail, *, confirm_token: Token) -> None:
        ...


class RegistrationService:
    def __init__(
        self,
        *,
        storage: Storage,
        mailer: Mailer,
        token_generator: Iterator[Token],
        utcnow: Callable[[], datetime]
    ):
        self._storage = storage
        self._mailer = mailer
        self._token_generator = token_generator
        self._utcnow = utcnow

    def subscribe(self, email: EMail):
        registration = self._storage.find(email)
        if registration is None:
            registration = Registration(
                email=email,
                last_update=self._utcnow(),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
            )

        if registration.state == State.pending_subscribe:
            registration.last_update = self._utcnow()
            if registration.confirm_token is None:
                registration.confirm_token = next(self._token_generator)

            self._storage.upsert(registration)
            self._mailer.mail_subscribe_confirm(
                email, confirm_token=registration.confirm_token
            )
