from dataclasses import asdict
import datetime
from functools import cache
import json
from typing import Annotated, Literal, Optional, Union

from fastapi import Depends, FastAPI, Header, Request, status
from fastapi.responses import PlainTextResponse
from jinja2 import FileSystemLoader
from pydantic import BaseSettings
from tinydb import TinyDB

from doveseed.config import Config, SmtpConfig, TemplateVarsConfig

from .confirmation import EmailConfirmationRequester
from .email_templating import EmailFromTemplateProvider, FileSystemBinaryLoader
from .registration import (
    ConfirmationRequester,
    RegistrationService,
    UnauthorizedException,
)
from .smtp import ConnectionManager, noop_connection, smtp_connection
from .storage import TinyDbStorage
from .token_gen import gen_secure_token
from .domain_types import Email, Token


class Settings(BaseSettings):
    doveseed_config: str = "config.json"
    doveseed_env: Union[Literal["production"], Literal["development"]] = "production"


@cache
def get_config() -> Config:
    settings = Settings()
    with open(settings.doveseed_config, "r", encoding="utf-8") as f:
        config = json.load(f)
        if config.get("smtp", None):
            config["smtp"] = SmtpConfig(**config["smtp"])
        return Config(
            template_vars=TemplateVarsConfig(**config.pop("template_vars")), **config
        )


ConfigDependency = Annotated[Config, Depends(get_config)]


@cache
def get_db(config: ConfigDependency):
    return TinyDB(config.db)


@cache
def get_connection(config: ConfigDependency):
    return (
        smtp_connection(**asdict(config.smtp))
        if config.smtp is not None
        else noop_connection()
    )


@cache
def get_confirmation_requester(
    config: ConfigDependency,
    connection: Annotated[ConnectionManager, Depends(get_connection)],
):
    return EmailConfirmationRequester(
        connection=connection,
        message_provider=EmailFromTemplateProvider(
            settings=EmailFromTemplateProvider.Settings(**asdict(config.template_vars)),
            template_loader=FileSystemLoader(config.email_templates),
            binary_loader=FileSystemBinaryLoader(config.email_templates),
        ),
    )


@cache
def get_storage(db: Annotated[TinyDB, Depends(get_db)]):
    return TinyDbStorage(db)


@cache
def get_registration_service(
    confirmation_requester: Annotated[
        ConfirmationRequester, Depends(get_confirmation_requester)
    ],
    storage: Annotated[TinyDbStorage, Depends(get_storage)],
):
    return RegistrationService(
        storage=storage,
        confirmation_requester=confirmation_requester,
        token_generator=gen_secure_token(),
        utcnow=datetime.datetime.utcnow,
    )


def require_bearer_token(
    authorization: Annotated[Optional[str], Header()] = None
) -> Token:
    if authorization is None:
        raise UnauthorizedException("Improper Authorization header.")
    auth_type, token = authorization.split(" ", 1)
    if auth_type.lower() != "bearer":
        raise UnauthorizedException("Requires bearer authorization.")
    return Token.from_string(token)


app = FastAPI(
    openapi_url="/openapi.json" if Settings().doveseed_env == "development" else None
)


@app.get("/health", status_code=status.HTTP_204_NO_CONTENT)
async def health():
    pass


@app.post("/subscribe/{email}", status_code=status.HTTP_204_NO_CONTENT)
def subscribe(
    email: str,
    registration_service: Annotated[
        RegistrationService, Depends(get_registration_service)
    ],
):
    registration_service.subscribe(Email(email))


@app.post("/unsubscribe/{email}", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    email: str,
    registration_service: Annotated[
        RegistrationService, Depends(get_registration_service)
    ],
):
    registration_service.unsubscribe(Email(email))


@app.post("/confirm/{email}", status_code=status.HTTP_204_NO_CONTENT)
def confirm(
    email: str,
    registration_service: Annotated[
        RegistrationService, Depends(get_registration_service)
    ],
    token: Annotated[Token, Depends(require_bearer_token)],
):
    registration_service.confirm(Email(email), token)


@app.exception_handler(UnauthorizedException)
def handle_unauthorized_exception(request: Request, exc: UnauthorizedException):
    return PlainTextResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=str(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )
