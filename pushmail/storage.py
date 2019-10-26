from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from inspect import isclass
from typing import Optional

from tinydb import TinyDB, Query

from .registration import EMail, Registration


class TinyDbStorage:
    def __init__(self, tinydb: TinyDB):
        self._tinydb = tinydb

    def upsert(self, registration: Registration) -> None:
        data = asdict(registration)
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
            elif isinstance(v, Enum):
                data[k] = v.name
        self._tinydb.upsert(data, Query().email == registration.email)

    def find(self, email: EMail) -> Optional[Registration]:
        data = self._tinydb.get(Query().email == email)
        if data is None:
            return None

        for field in fields(Registration):
            if field.type is datetime:
                data[field.name] = datetime.fromisoformat(data[field.name])
            elif isclass(field.type) and issubclass(field.type, Enum):
                data[field.name] = field.type[data[field.name]]
        return Registration(**data)

    def delete(self, email: EMail) -> None:
        self._tinydb.remove(Query().email == email)
