import http
from typing import Dict

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from doveseed.app import create_app_from_instances
from doveseed.domain_types import Email, Token, Action


class ConfirmationRequester:
    def __init__(self):
        self.tokens: Dict[Email, str] = {}

    def request_confirmation(
        self, email: Email, *, action: Action, confirm_token: Token
    ):
        self.tokens[email] = confirm_token.to_string()


def assert_success(response):
    assert 200 <= response.status_code < 300, response.data


@pytest.fixture
def confirmation_requester():
    return ConfirmationRequester()


@pytest.fixture
def db():
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def client(db, confirmation_requester):
    app = create_app_from_instances(db, confirmation_requester)
    with app.test_client() as client:
        yield client


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
    assert unknown_email_response.status_code == http.HTTPStatus.UNAUTHORIZED

    missing_auth_response = client.post(f"/confirm/{given_email}")
    assert missing_auth_response.status_code == http.HTTPStatus.UNAUTHORIZED

    assert (
        client.post(
            f"/confirm/non-{given_email}",
            headers=[
                ("Authorization", "Basic " + confirmation_requester.tokens[given_email])
            ],
        )
    ).status_code == http.HTTPStatus.UNAUTHORIZED

    known_email_response = client.post(
        f"/confirm/non-{given_email}",
        headers=[("Authorization", "Bearer invalid-token")],
    )
    assert known_email_response.status_code == http.HTTPStatus.UNAUTHORIZED

    assert known_email_response.data == unknown_email_response.data
