from datetime import datetime, timedelta

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from pushmail.registration import EMail, Registration, State
from pushmail.storage import TinyDbStorage


@pytest.fixture
def tiny_db():
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def tiny_db_storage(tiny_db):
    return TinyDbStorage(tiny_db)


class TestTinyDbStorage:
    def test_upsert_of_new_entity(self, tiny_db, tiny_db_storage):
        last_update = datetime(2019, 10, 25, 13, 37)
        registration = Registration(
            email=EMail("mail@test.org"),
            last_update=last_update,
            state=State.subscribed,
        )

        tiny_db_storage.upsert(registration)

        assert tiny_db.get(Query().email == "mail@test.org") == {
            "email": "mail@test.org",
            "last_update": last_update.isoformat(),
            "state": "subscribed",
            "confirm_action": None,
            "confirm_token": None,
            "immediate_unsubscribe_token": None,
        }

    def test_upsert_of_existing_entity(self, tiny_db, tiny_db_storage):
        first_update = datetime(2019, 10, 25, 13, 37)
        registration = Registration(
            email=EMail("mail@test.org"),
            last_update=first_update,
            state=State.subscribed,
        )

        tiny_db_storage.upsert(registration)

        last_update = first_update + timedelta(days=1)
        registration.last_update = last_update
        tiny_db_storage.upsert(registration)

        assert tiny_db.get(Query().email == "mail@test.org") == {
            "email": "mail@test.org",
            "last_update": last_update.isoformat(),
            "state": "subscribed",
            "confirm_action": None,
            "confirm_token": None,
            "immediate_unsubscribe_token": None,
        }
