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


class ConfirmationRequester(Protocol):
    def request_confirmation(
        self, email: EMail, *, action: Action, confirm_token: Token
    ) -> None:
        ...


class RegistrationService:
    def __init__(
        self,
        *,
        storage: Storage,
        confirmation_requester: ConfirmationRequester,
        token_generator: Iterator[Token],
        utcnow: Callable[[], datetime]
    ):
        self._storage = storage
        self._confirmation_requester = confirmation_requester
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

            self._perform_state_change_requiring_confirmation(registration)

    def unsubscribe(self, email: EMail):
        registration = self._storage.find(email)
        subscribed_states = (State.subscribed, State.pending_unsubscribe)
        if registration is not None and registration.state in subscribed_states:
            registration.state = State.pending_unsubscribe
            registration.last_update = self._utcnow()
            registration.confirm_token = next(self._token_generator)
            registration.confirm_action = Action.unsubscribe
            self._perform_state_change_requiring_confirmation(registration)

    def confirm(self, email: EMail, token: Token):
        registration = self._storage.find(email)

        if registration is None or registration.confirm_token != token:
            raise UnauthorizedException("Invalid token.")

        registration.state = State.subscribed
        registration.last_update = self._utcnow()
        registration.confirm_token = None
        registration.confirm_action = None
        self._storage.upsert(registration)

    def _perform_state_change_requiring_confirmation(self, registration):
        self._storage.upsert(registration)
        self._confirmation_requester.request_confirmation(
            registration.email,
            action=registration.confirm_action,
            confirm_token=registration.confirm_token,
        )


class UnauthorizedException(Exception):
    pass
