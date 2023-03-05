import datetime
import http
import json
import os

from flask import Flask, request
from flask_cors import CORS
from jinja2 import FileSystemLoader
from tinydb import TinyDB

from .confirmation import EmailConfirmationRequester
from .email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader
from .registration import (
    ConfirmationRequester,
    RegistrationService,
    UnauthorizedException,
)
from .smtp import noop_connection, smtp_connection
from .storage import TinyDbStorage
from .token_gen import gen_secure_token
from .domain_types import Email, Token


def create_app_from_config(config_filename: str) -> Flask:
    with open(config_filename, "r", encoding="utf-8") as f:
        config = json.load(f)
    db = TinyDB(config["db"])
    connection = (
        smtp_connection(**config["smtp"])
        if config["smtp"] is not None
        else noop_connection()
    )
    confirmation_requester = EmailConfirmationRequester(
        connection=connection,
        message_provider=EmailFromTemplateProvider(
            settings=EmailFromTemplateProvider.Settings(**config["template_vars"]),
            template_loader=FileSystemLoader(config["email_templates"]),
            binary_loader=FileSystemBinaryLoader(config["email_templates"]),
        ),
    )
    app = create_app_from_instances(db, confirmation_requester)
    if "cors" in config:
        CORS(app, **config["cors"])
    return app


def create_app_from_instances(
    db: TinyDB, confirmation_requester: ConfirmationRequester
) -> Flask:
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
            return Token.from_string(token)
        except (KeyError, ValueError) as err:
            raise UnauthorizedException("Improper Authorization header.") from err

    app = Flask("doveseed")

    @app.route("/health", methods=["GET"])
    def health():
        return "", http.HTTPStatus.NO_CONTENT

    @app.route("/subscribe/<email>", methods=["POST"])
    def subscribe(email: str):
        registration_service.subscribe(Email(email))
        return "", http.HTTPStatus.NO_CONTENT

    @app.route("/unsubscribe/<email>", methods=["POST"])
    def unsubscribe(email: str):
        registration_service.unsubscribe(Email(email))
        return "", http.HTTPStatus.NO_CONTENT

    @app.route("/confirm/<email>", methods=["POST"])
    def confirm(email: str):
        try:
            token = require_bearer_token()
            registration_service.confirm(Email(email), token)
            return "", http.HTTPStatus.NO_CONTENT
        except UnauthorizedException as err:
            return (
                str(err),
                http.HTTPStatus.UNAUTHORIZED,
                {"WWW-Authenticate": "Bearer"},
            )

    return app


def create_app() -> Flask:
    return create_app_from_config(os.environ.get("DOVESEED_CONFIG", "config.json"))
