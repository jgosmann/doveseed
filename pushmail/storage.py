from base64 import b64decode, b64encode
from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from inspect import isclass
from typing import Optional, Union

from tinydb import TinyDB, Query

from .registration import Registration
from pushmail.types import Email


class TinyDbStorage:
    def __init__(self, tinydb: TinyDB):
        self._tinydb = tinydb

    def upsert(self, registration: Registration) -> None:
        data = asdict(registration)
        for k, value in data.items():
            if isinstance(value, bytes):
                data[k] = b64encode(value).decode("ascii")
            elif isinstance(value, datetime):
                data[k] = value.isoformat()
            elif isinstance(value, Enum):
                data[k] = value.name
        self._tinydb.upsert(data, Query().email == registration.email)

    def find(self, email: Email) -> Optional[Registration]:
        data = self._tinydb.get(Query().email == email)
        if data is None:
            return None

        for field in fields(Registration):
            if data[field.name] is None:
                continue

            type_info = field.type
            if getattr(type_info, "__origin__", None) is Union:
                type_info = next(x for x in type_info.__args__ if x is not type(None))

            if getattr(type_info, "__supertype__", None) is bytes:
                data[field.name] = type_info(
                    b64decode(data[field.name].encode("ascii"))
                )
            elif type_info is datetime:
                data[field.name] = datetime.fromisoformat(data[field.name])
            elif isclass(type_info) and issubclass(type_info, Enum):
                data[field.name] = type_info[data[field.name]]

        return Registration(**data)

    def delete(self, email: Email) -> None:
        self._tinydb.remove(Query().email == email)
