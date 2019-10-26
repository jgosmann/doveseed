from datetime import datetime
import itertools

import pytest

from pushmail.registration import (
    Action,
    EMail,
    Registration,
    RegistrationService,
    State,
)


class InMemoryStorage:
    def __init__(self):
        self.data = {}

    def insert(self, registration: Registration):
        self.data[registration.email] = registration

    def find(self, email: EMail) -> Registration:
        return self.data[email]


class MockTokenGenerator:
    def __init__(self):
        self.generated_tokens = []

    def __iter__(self):
        return self

    def __next__(self):
        self.generated_tokens.append('token' + str(len(self.generated_tokens)))
        return self.generated_tokens[-1]


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def token_generator():
    return MockTokenGenerator()


@pytest.fixture
def utcnow():
    return lambda: datetime(2019, 10, 25, 13, 37)


@pytest.fixture
def registration_service(storage, token_generator, utcnow):
    return RegistrationService(
        storage=storage, token_generator=token_generator, utcnow=utcnow
    )


class TestRegistrationServiceSubscribe:
    def test_creates_new_registration_for_non_existing_mail(
        self, registration_service, storage, token_generator, utcnow
    ):
        given_email = EMail("new@test.org")
        registration_service.subscribe(given_email)
        stored = storage.find(given_email)
        assert stored == Registration(
            email=given_email,
            state=State.pending_subscribe,
            last_update=utcnow(),
            confirm_token=token_generator.generated_tokens[0],
            confirm_action=Action.subscribe,
            immediate_unsubscribe_token=None,
        )
