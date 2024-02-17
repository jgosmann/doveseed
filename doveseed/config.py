from dataclasses import dataclass
from typing import Literal, Optional, Union


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    user: str
    password: str
    port: int = 0
    ssl_mode: Union[Literal["no-ssl"], Literal["start-tls"], Literal["tls"]] = (
        "start-tls"
    )
    check_hostname: bool = True


@dataclass(frozen=True)
class TemplateVarsConfig:
    display_name: str
    host: str
    sender: str
    confirm_url_format: str = "https://{host}/confirm/{email}?token={token}"


@dataclass(frozen=True)
class Config:
    db: str
    rss: str
    template_vars: TemplateVarsConfig
    email_templates: str
    confirm_timeout_minutes: int
    smtp: Optional[SmtpConfig] = None
