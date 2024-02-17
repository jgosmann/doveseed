from typing import Dict
from httpx import Response

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from doveseed.app import app, get_confirmation_requester, get_db
from doveseed.domain_types import Email, Token, Action


class ConfirmationRequester:
    def __init__(self):
        self.tokens: Dict[Email, str] = {}

    def request_confirmation(
        self, email: Email, *, action: Action, confirm_token: Token
    ):
        self.tokens[email] = confirm_token.to_string()


def assert_success(response: Response):
    assert 200 <= response.status_code < 300, response.read()


@pytest.fixture
def confirmation_requester():
    return ConfirmationRequester()


@pytest.fixture
def db():
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def client(db, confirmation_requester):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_confirmation_requester] = (
        lambda: confirmation_requester
    )
    yield TestClient(app)
    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_confirmation_requester]


def test_subscription_and_unsubscription_flow(client, db, confirmation_requester):
    given_email = Email("foo@test.org")
    assert_success(client.post(f"/subscribe/{given_email}"))
    assert_success(
        client.post(
            f"/confirm/{given_email}",
            headers=[
                (
                    "Authorization",
                    "Bearer " + confirmation_requester.tokens[given_email],
                )
            ],
        )
    )

    assert db.get(Query().email == given_email)["state"] == "subscribed"

    assert_success(client.post(f"/unsubscribe/{given_email}"))
    assert_success(
        client.post(
            f"/confirm/{given_email}",
            headers=[
                (
                    "Authorization",
                    "Bearer " + confirmation_requester.tokens[given_email],
                )
            ],
        )
    )

    assert db.get(Query().email == given_email) is None


def test_confirm_unauthorized(client, db, confirmation_requester):
    given_email = Email("foo@test.org")
    assert_success(client.post(f"/subscribe/{given_email}"))

    unknown_email_response = client.post(
        f"/confirm/non-{given_email}",
        headers=[
            ("Authorization", "Bearer " + confirmation_requester.tokens[given_email])
        ],
    )
    assert unknown_email_response.status_code == status.HTTP_401_UNAUTHORIZED

    missing_auth_response = client.post(f"/confirm/{given_email}")
    assert missing_auth_response.status_code == status.HTTP_401_UNAUTHORIZED

    assert (
        client.post(
            f"/confirm/non-{given_email}",
            headers=[
                ("Authorization", "Basic " + confirmation_requester.tokens[given_email])
            ],
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    known_email_response = client.post(
        f"/confirm/non-{given_email}",
        headers=[("Authorization", "Bearer invalid-token")],
    )
    assert known_email_response.status_code == status.HTTP_401_UNAUTHORIZED

    assert known_email_response.read() == unknown_email_response.read()
