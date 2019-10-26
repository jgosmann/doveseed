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

    def test_find_of_non_exsting_entity_returns_none(self, tiny_db_storage):
        assert tiny_db_storage.find(EMail("unknown@test.org")) is None

    def test_find_returns_matching_entity(self, tiny_db, tiny_db_storage):
        last_update = datetime(2019, 10, 25, 13, 37)
        tiny_db.insert(
            {
                "email": "mail@test.org",
                "last_update": last_update.isoformat(),
                "state": "subscribed",
                "confirm_action": None,
                "confirm_token": None,
                "immediate_unsubscribe_token": None,
            }
        )

        assert tiny_db_storage.find(EMail("mail@test.org")) == Registration(
            email=EMail("mail@test.org"),
            last_update=last_update,
            state=State.subscribed,
        )

    def test_delete_existing_entity(self, tiny_db, tiny_db_storage):
        tiny_db.insert(
            {
                "email": "mail@test.org",
                "last_update": datetime(2019, 10, 25, 13, 37).isoformat(),
                "state": "subscribed",
                "confirm_action": None,
                "confirm_token": None,
                "immediate_unsubscribe_token": None,
            }
        )

        tiny_db_storage.delete(EMail("mail@test.org"))

        assert tiny_db.get(Query().email == "mail@test.org") is None

    def test_delete_non_existing_entity(self, tiny_db, tiny_db_storage):
        tiny_db_storage.delete(EMail("mail@test.org"))
        assert tiny_db.get(Query().email == "mail@test.org") is None
