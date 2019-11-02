from datetime import datetime, timedelta
import itertools
from unittest.mock import MagicMock
from typing import cast, Dict, List, Optional

import pytest

from doveseed.registration import (
    ConfirmationRequester,
    Registration,
    RegistrationService,
    UnauthorizedException,
)
from doveseed.types import Email, Token, State, Action


class InMemoryStorage:
    def __init__(self):
        self.data: Dict[Email, Registration] = {}

    def upsert(self, registration: Registration):
        self.data[registration.email] = registration

    def find(self, email: Email) -> Optional[Registration]:
        if email in self.data:
            return self.data[email]
        return None

    def delete(self, email: Email) -> None:
        del self.data[email]


class MockTokenGenerator:
    def __init__(self):
        self.generated_tokens: List[Token] = []

    def __iter__(self):
        return self

    def __next__(self):
        self.generated_tokens.append(
            Token(b"token" + bytes(len(self.generated_tokens)))
        )
        return self.generated_tokens[-1]


class MockConfirmationRequester:
    def __init__(self):
        self.request_confirmation = MagicMock()


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def confirmation_requester():
    return MockConfirmationRequester()


@pytest.fixture
def token_generator():
    return MockTokenGenerator()


NOW = datetime(2019, 10, 25, 13, 37)


@pytest.fixture
def utcnow():
    return lambda: NOW


@pytest.fixture
def registration_service(storage, confirmation_requester, token_generator, utcnow):
    return RegistrationService(
        storage=storage,
        confirmation_requester=confirmation_requester,
        token_generator=token_generator,
        utcnow=utcnow,
    )


class TestRegistrationServiceSubscribe:
    def test_if_email_unknown_creates_registration(
        self, registration_service, storage, token_generator, utcnow
    ):
        given_email = Email("new@test.org")
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

    def test_if_email_unknown_sends_subscription_confirm_mail(
        self, registration_service, confirmation_requester, token_generator, utcnow
    ):
        given_email = Email("new@test.org")
        registration_service.subscribe(given_email)
        confirmation_requester.request_confirmation.assert_called_with(
            given_email,
            action=Action.subscribe,
            confirm_token=token_generator.generated_tokens[0],
        )

    def test_if_subscription_is_pending_bumps_last_update(
        self, registration_service, storage, token_generator, utcnow
    ):
        given_email = Email("pending@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.pending_subscribe,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=next(token_generator),
                confirm_action=Action.subscribe,
                immediate_unsubscribe_token=None,
            )
        )

        registration_service.subscribe(given_email)

        stored = storage.find(given_email)
        assert stored == Registration(
            email=given_email,
            state=State.pending_subscribe,
            last_update=utcnow(),
            confirm_token=token_generator.generated_tokens[0],
            confirm_action=Action.subscribe,
        )

    def test_if_subscription_is_pending_resends_confirm_mail(
        self,
        registration_service,
        storage,
        confirmation_requester,
        token_generator,
        utcnow,
    ):
        given_email = Email("pending@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.pending_subscribe,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=next(token_generator),
                confirm_action=Action.subscribe,
            )
        )

        registration_service.subscribe(given_email)

        confirmation_requester.request_confirmation.assert_called_with(
            given_email,
            action=Action.subscribe,
            confirm_token=token_generator.generated_tokens[0],
        )

    @pytest.mark.parametrize("state", (State.subscribed, State.pending_unsubscribe))
    def test_if_subscribed_no_effect(
        self,
        state,
        registration_service,
        storage,
        confirmation_requester,
        token_generator,
        utcnow,
    ):
        given_email = Email("subscribed@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=state,
                last_update=utcnow() - timedelta(days=1),
                immediate_unsubscribe_token=Token(b"token"),
            )
        )

        registration_service.subscribe(given_email)

        stored = storage.find(given_email)
        assert not confirmation_requester.request_confirmation.called
        assert stored == Registration(
            email=given_email,
            state=state,
            last_update=utcnow() - timedelta(days=1),
            immediate_unsubscribe_token=Token(b"token"),
        )


class TestRegistrationServiceUnsubscribe:
    def test_if_email_is_unkown_has_no_effect(
        self, registration_service, confirmation_requester
    ):
        given_email = Email("unkown@test.org")
        registration_service.unsubscribe(given_email)
        assert not confirmation_requester.request_confirmation.called

    def test_if_subscription_pending_has_no_effect(
        self, registration_service, storage, confirmation_requester, utcnow
    ):
        given_email = Email("pending@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.pending_subscribe,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=Token(b"token"),
                confirm_action=Action.subscribe,
            )
        )

        registration_service.unsubscribe(given_email)

        stored = storage.find(given_email)
        assert not confirmation_requester.request_confirmation.called
        assert stored == Registration(
            email=given_email,
            state=State.pending_subscribe,
            last_update=utcnow() - timedelta(days=1),
            confirm_token=Token(b"token"),
            confirm_action=Action.subscribe,
        )

    @pytest.mark.parametrize("state", (State.subscribed, State.pending_unsubscribe))
    def test_if_subscribed_sets_registration_to_pending_unsubscribe(
        self, state, registration_service, storage, token_generator, utcnow
    ):
        given_email = Email("subscribed@test.org")
        storage.upsert(
            Registration(
                email=given_email, state=state, last_update=utcnow() - timedelta(days=1)
            )
        )

        registration_service.unsubscribe(given_email)

        stored = storage.find(given_email)
        assert stored == Registration(
            email=given_email,
            state=State.pending_unsubscribe,
            last_update=utcnow(),
            confirm_token=token_generator.generated_tokens[0],
            confirm_action=Action.unsubscribe,
        )

    @pytest.mark.parametrize("state", (State.subscribed, State.pending_unsubscribe))
    def test_if_subscribed_requests_confirmation(
        self,
        state,
        registration_service,
        storage,
        confirmation_requester,
        token_generator,
        utcnow,
    ):
        given_email = Email("subscribed@test.org")
        storage.upsert(
            Registration(
                email=given_email, state=state, last_update=utcnow() - timedelta(days=1)
            )
        )

        registration_service.unsubscribe(given_email)

        confirmation_requester.request_confirmation.assert_called_with(
            given_email,
            action=Action.unsubscribe,
            confirm_token=token_generator.generated_tokens[0],
        )


class TestRegistrationServiceConfirm:
    def test_confirm_with_valid_token_activates_subscription(
        self, registration_service, storage, utcnow
    ):
        given_email = Email("pending@test.org")
        given_token = Token(b"token")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.pending_subscribe,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=given_token,
                confirm_action=Action.subscribe,
            )
        )

        registration_service.confirm(given_email, given_token)

        stored = storage.find(given_email)
        assert stored == Registration(
            email=given_email,
            state=State.subscribed,
            last_update=utcnow(),
            confirm_token=None,
            confirm_action=None,
        )

    def test_confirm_with_valid_token_removes_subscription(
        self, registration_service, storage, utcnow
    ):
        given_email = Email("pending@test.org")
        given_token = Token(b"token")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.pending_unsubscribe,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=given_token,
                confirm_action=Action.unsubscribe,
            )
        )

        registration_service.confirm(given_email, given_token)

        assert storage.find(given_email) is None

    @pytest.mark.parametrize(
        "state", (State.pending_subscribe, State.pending_unsubscribe)
    )
    def test_confirm_with_invalid_token_raises_exception(
        self, state, registration_service, storage, utcnow
    ):
        given_email = Email("pending@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=state,
                last_update=utcnow() - timedelta(days=1),
                confirm_token=Token(b"actual token"),
                confirm_action=Action.subscribe
                if state == State.pending_subscribe
                else Action.unsubscribe,
            )
        )

        with pytest.raises(UnauthorizedException):
            registration_service.confirm(given_email, Token(b"invalid token"))

    def test_confirm_for_unknown_email_raises_exception(self, registration_service):
        given_email = Email("pending@test.org")

        with pytest.raises(UnauthorizedException):
            registration_service.confirm(given_email, Token(b"token"))

    def test_confirm_for_registration_without_confirm_action_raises_exception(
        self, registration_service, storage, utcnow
    ):
        given_email = Email("subscribed@test.org")
        storage.upsert(
            Registration(
                email=given_email,
                state=State.subscribed,
                last_update=utcnow() - timedelta(days=1),
            )
        )

        with pytest.raises(UnauthorizedException):
            registration_service.confirm(given_email, None)
