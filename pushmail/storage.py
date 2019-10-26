from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from inspect import isclass
from typing import Optional, Union

from tinydb import TinyDB, Query

from .registration import EMail, Registration


class TinyDbStorage:
    def __init__(self, tinydb: TinyDB):
        self._tinydb = tinydb

    def upsert(self, registration: Registration) -> None:
        data = asdict(registration)
        for k, value in data.items():
            if isinstance(value, datetime):
                data[k] = value.isoformat()
            elif isinstance(value, Enum):
                data[k] = value.name
        self._tinydb.upsert(data, Query().email == registration.email)

    def find(self, email: EMail) -> Optional[Registration]:
        data = self._tinydb.get(Query().email == email)
        if data is None:
            return None

        for field in fields(Registration):
            type_info = field.type
            if getattr(type_info, "__origin__", None) is Union:
                type_info = next(x for x in type_info.__args__ if x is not type(None))
            if type_info is datetime:
                data[field.name] = datetime.fromisoformat(data[field.name])
            elif (
                isclass(type_info)
                and issubclass(type_info, Enum)
                and data[field.name] is not None
            ):
                data[field.name] = type_info[data[field.name]]
        return Registration(**data)

    def delete(self, email: EMail) -> None:
        self._tinydb.remove(Query().email == email)
