from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType, Optional


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


class RegistrationService:
    def __init__(self, *, storage, token_generator, utcnow):
        self.storage = storage
        self.token_generator = token_generator
        self.utcnow = utcnow

    def subscribe(self, email: EMail):
        registration = Registration(
            email=email,
            last_update=self.utcnow(),
            state=State.pending_subscribe,
            confirm_token=next(self.token_generator),
            confirm_action=Action.subscribe)
        self.storage.insert(registration)
