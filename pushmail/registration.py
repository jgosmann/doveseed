from datetime import datetime
from enum import Enum
from typing import NewType


EMail = NewType('EMail', str)
Token = NewType('Token', bytes)

State = Enum(
    'State', ('pending_subscribe', 'subscribed', 'pending_unsubscribe'))
Action = Enum('Action', ('subscribe', 'unsubscribe'))


class Registration:
    def __init__(
            self,
            *,
            email: EMail,
            last_update: datetime,
            state: State = State.pending_subscribe,
            confirm_token: Token = None,
            confirm_action: Action = None,
            immediate_unsubscribe_token: Token = None):
        self.email = email
        self.last_update = last_update
        self.state = state
        self.confirm_token = confirm_token
        self.confirm_action = confirm_action
        self.immediate_unsubscribe_token = immediate_unsubscribe_token


class RegistrationService:
    def __init__(self, *, storage, token_generator, utcnow):
        self.storage = storage
        self.token_generator = token_generator
        self.utcnow = utcnow

    def subscribe(self, email: EMail):
        raise NotImplementedError()
