from dataclasses import asdict
from datetime import datetime
from enum import Enum
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
        pass

    def delete(self, email: EMail) -> None:
        pass
