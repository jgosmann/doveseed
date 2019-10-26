from datetime import datetime
import itertools

import pytest

from pushmail.registration import Action, EMail, Registration, RegistrationService, State


class InMemoryStorage:
    def __init__(self):
        self.data = {}

    def insert(self, registration: Registration):
        self.data[registration.email] = registration

    def find(self, email: EMail) -> Registration:
        return self.data[email]


@pytest.fixture
def storage():
    return InMemoryStorage()

@pytest.fixture
def token_generator():
    def gen():
        for i in itertools.count():
            yield 'token' + str(i)
    return gen

@pytest.fixture
def utcnow():
    return datetime(2019, 10, 25, 13, 37)

@pytest.fixture
def registration_service(storage, token_generator, utcnow):
    return RegistrationService(
        storage=storage, token_generator=token_generator, utcnow=utcnow)


class TestRegistrationServiceSubscribe:
    def test_creates_new_registration_for_non_existing_mail(
            self, registration_service, storage):
        given_email = EMail('new@test.org')
        registration_service.subscribe(given_email)
        stored = storage.find(given_email)
        assert stored == Registration(
            email=given_email,
            state=State.pending_subscribe,
            last_update=utcnow(),
            confirm_token=next(token_generator()()),
            confirm_action=Action.subscribe,
            immediate_unsubscribe_token=None)
