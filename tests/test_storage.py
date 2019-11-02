from datetime import datetime, timedelta

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from pushmail.registration import Registration
from pushmail.types import Email, Token, State, Action
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
            email=Email("mail@test.org"),
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
            email=Email("mail@test.org"),
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
        assert tiny_db_storage.find(Email("unknown@test.org")) is None

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

        assert tiny_db_storage.find(Email("mail@test.org")) == Registration(
            email=Email("mail@test.org"),
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

        tiny_db_storage.delete(Email("mail@test.org"))

        assert tiny_db.get(Query().email == "mail@test.org") is None

    def test_delete_non_existing_entity(self, tiny_db, tiny_db_storage):
        tiny_db_storage.delete(Email("mail@test.org"))
        assert tiny_db.get(Query().email == "mail@test.org") is None

    @pytest.mark.parametrize(
        "instance",
        (
            Registration(
                email=Email("mail@test.org"),
                last_update=datetime(2019, 10, 25, 13, 37),
                state=State.subscribed,
                confirm_action=None,
                confirm_token=None,
                immediate_unsubscribe_token=None,
            ),
            Registration(
                email=Email("mail2@test.org"),
                last_update=datetime(2019, 10, 25, 13, 38),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
                confirm_token=Token(b"token"),
                immediate_unsubscribe_token=Token(b"another token"),
            ),
        ),
    )
    def test_roundtrip(self, instance, tiny_db_storage):
        tiny_db_storage.upsert(instance)
        assert tiny_db_storage.find(instance.email) == instance
