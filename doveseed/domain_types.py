from base64 import b64encode, b64decode
from datetime import datetime
from typing import Optional

from dataclasses import dataclass
from enum import Enum
from typing import NewType, Type, TypeVar

Email = NewType("Email", str)
State = Enum("State", ("pending_subscribe", "subscribed", "pending_unsubscribe"))
Action = Enum("Action", ("subscribe", "unsubscribe"))

_T = TypeVar("_T", bound="Token")


@dataclass
class FeedItem:
    title: str
    link: str
    pub_date: datetime
    description: str
    image: Optional[str]


@dataclass
class Token:
    data: bytes

    @classmethod
    def from_string(cls: Type[_T], value: str) -> _T:
        return cls(data=b64decode(value.encode("ascii")))

    def to_string(self) -> str:
        return b64encode(self.data).decode("ascii")
