from base64 import b64decode, b64encode
from collections.abc import Mapping
from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from enum import Enum
from inspect import isclass
from typing import Any, Dict, Optional, Type, Union

from tinydb import TinyDB, Query

from .domain_types import Email, State
from .registration import Registration


class TinyDbStorage:
    def __init__(self, tinydb: TinyDB):
        self._tinydb = tinydb

    def all(self):
        for data in self._tinydb.all():
            self._deserialize_in_place(Registration, data)
            yield Registration(**data)

    def upsert(self, registration: Registration) -> None:
        data = asdict(registration)
        self._serialize_in_place(data)
        self._tinydb.upsert(data, Query().email == registration.email)

    def _serialize_in_place(self, data: Dict[str, Any]):
        for k, value in data.items():
            if isinstance(value, Mapping):
                self._serialize_in_place(data[k])
            if isinstance(value, bytes):
                data[k] = b64encode(value).decode("ascii")
            elif isinstance(value, datetime):
                data[k] = value.isoformat()
            elif isinstance(value, Enum):
                data[k] = value.name

    def find(self, email: Email) -> Optional[Registration]:
        data = self._tinydb.get(Query().email == email)
        if data is None:
            return None
        self._deserialize_in_place(Registration, data)
        return Registration(**data)

    def _deserialize_in_place(self, to_type: Type, data: Dict[str, Any]):
        for field in fields(to_type):
            if data[field.name] is None:
                continue

            type_info = field.type
            if getattr(type_info, "__origin__", None) is Union:
                type_info = next(x for x in type_info.__args__ if x is not type(None))

            if type_info is bytes:
                data[field.name] = type_info(
                    b64decode(data[field.name].encode("ascii"))
                )
            elif type_info is datetime:
                data[field.name] = datetime.fromisoformat(data[field.name])
            elif isclass(type_info) and issubclass(type_info, Enum):
                data[field.name] = type_info[data[field.name]]
            elif is_dataclass(type_info):
                self._deserialize_in_place(type_info, data[field.name])
                data[field.name] = type_info(**data[field.name])

    def delete(self, email: Email) -> None:
        self._tinydb.remove(Query().email == email)

    def drop_old_unconfirmed(self, *, drop_before: datetime):
        is_before = lambda v: datetime.fromisoformat(v) < drop_before
        registration = Query()
        self._tinydb.remove(
            registration.last_update.test(is_before)
            & (registration.state == State.pending_subscribe.name)
        )

    def get_last_seen(self):
        try:
            return datetime.fromisoformat(
                self._tinydb.get(Query().key == "last_seen")["value"]
            )
        except (KeyError, TypeError):
            return None

    def set_last_seen(self, value: datetime):
        self._tinydb.upsert(
            {"key": "last_seen", "value": value.isoformat()}, Query().key == "last_seen"
        )

    def get_all_active_subscribers(self):
        registration = Query()
        subscribers = self._tinydb.search(
            (registration.state == State.subscribed.name)
            | (registration.state == State.pending_unsubscribe.name)
        )
        for subscriber in subscribers:
            self._deserialize_in_place(Registration, subscriber)
            yield Registration(**subscriber)
