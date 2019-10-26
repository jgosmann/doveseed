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
    confirm_token: Token
    confirm_action: Action
    immediate_unsubscribe_token: Optional[Token] = None


class Storage(Protocol):
    def insert(self, registration: Registration) -> None:
        ...


class RegistrationService:
    def __init__(
        self,
        *,
        storage: Storage,
        token_generator: Iterator[Token],
        utcnow: Callable[[], datetime]
    ):
        self.storage = storage
        self.token_generator = token_generator
        self.utcnow = utcnow

    def subscribe(self, email: EMail):
        registration = Registration(
            email=email,
            last_update=self.utcnow(),
            state=State.pending_subscribe,
            confirm_token=next(self.token_generator),
            confirm_action=Action.subscribe,
        )
        self.storage.insert(registration)
