from base64 import b64decode
import datetime
import http
from typing import Optional

from flask import Flask, request
from tinydb import TinyDB

from .registration import RegistrationService, UnauthorizedException
from pushmail.types import EMail, Token
from .storage import TinyDbStorage
from .token_gen import gen_secure_token


class ConfirmationRequester:
    def request_confirmation(self, *args, **kwargs):
        return None


def create_app(
    db: Optional[TinyDB] = None,
    confirmation_requester: Optional[ConfirmationRequester] = None,
):
    if db is None:
        db = TinyDB("test.json")
    if confirmation_requester is None:
        confirmation_requester = ConfirmationRequester()

    storage = TinyDbStorage(db)
    registration_service = RegistrationService(
        storage=storage,
        confirmation_requester=confirmation_requester,
        token_generator=gen_secure_token(),
        utcnow=datetime.datetime.utcnow,
    )

    def require_bearer_token() -> Token:
        try:
            auth_type, token = request.headers["Authorization"].split(" ", 1)
            if auth_type.lower() != "bearer":
                raise UnauthorizedException("Requires bearer authorization.")
            return Token(b64decode(token.encode("ascii")))
        except (KeyError, ValueError):
            raise UnauthorizedException("Improper Authorization header.")

    app = Flask("pushmail")

    @app.route("/subscribe/<email>", methods=["POST"])
    def subscribe(email: str):
        registration_service.subscribe(EMail(email))
        return "", http.HTTPStatus.NO_CONTENT

    @app.route("/unsubscribe/<email>", methods=["POST"])
    def unsubscribe(email: str):
        registration_service.unsubscribe(EMail(email))
        return "", http.HTTPStatus.NO_CONTENT

    @app.route("/confirm/<email>", methods=["POST"])
    def confirm(email: str):
        try:
            token = require_bearer_token()
            registration_service.confirm(EMail(email), token)
            return "", http.HTTPStatus.NO_CONTENT
        except UnauthorizedException as err:
            return (
                str(err),
                http.HTTPStatus.UNAUTHORIZED,
                {"WWW-Authenticate": "Bearer"},
            )

    return app
