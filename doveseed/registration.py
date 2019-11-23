from dataclasses import dataclass
from datetime import datetime
from email.utils import getaddresses
from typing import Callable, Iterator, Optional

from typing_extensions import Protocol

from .domain_types import Email, Token, State, Action


@dataclass
class Registration:
    email: Email
    last_update: datetime
    state: State
    confirm_token: Optional[Token] = None
    confirm_action: Optional[Action] = None


class Storage(Protocol):
    def upsert(self, registration: Registration) -> None:
        ...

    def find(self, email: Email) -> Optional[Registration]:
        ...

    def delete(self, email: Email) -> None:
        ...


class ConfirmationRequester(Protocol):
    def request_confirmation(
        self, email: Email, *, action: Action, confirm_token: Token
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

    def subscribe(self, email: Email):
        self._check_email(email)
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

    def unsubscribe(self, email: Email):
        self._check_email(email)
        registration = self._storage.find(email)
        subscribed_states = (State.subscribed, State.pending_unsubscribe)
        if registration is not None and registration.state in subscribed_states:
            registration.state = State.pending_unsubscribe
            registration.last_update = self._utcnow()
            registration.confirm_token = next(self._token_generator)
            registration.confirm_action = Action.unsubscribe
            self._perform_state_change_requiring_confirmation(registration)

    def confirm(self, email: Email, token: Token):
        registration = self._storage.find(email)

        if (
            registration is None
            or registration.confirm_action is None
            or registration.confirm_token != token
        ):
            raise UnauthorizedException("Invalid token.")

        if registration.confirm_action == Action.subscribe:
            registration.state = State.subscribed
            registration.last_update = self._utcnow()
            registration.confirm_token = None
            registration.confirm_action = None
            self._storage.upsert(registration)
        elif registration.confirm_action == Action.unsubscribe:
            self._storage.delete(email)

    def _perform_state_change_requiring_confirmation(self, registration):
        self._storage.upsert(registration)
        self._confirmation_requester.request_confirmation(
            registration.email,
            action=registration.confirm_action,
            confirm_token=registration.confirm_token,
        )

    def _check_email(self, email: Email):
        addresses = getaddresses([email])
        if len(addresses) != 1 or addresses[0][1] != email:
            raise ValueError("Must provide exactly one valid email address.")


class UnauthorizedException(Exception):
    pass
