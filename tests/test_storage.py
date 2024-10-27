from datetime import datetime, timedelta, timezone

import pytest
from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

from doveseed.domain_types import Action, Email, State, Token
from doveseed.registration import Registration
from doveseed.storage import TinyDbStorage


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
            ),
            Registration(
                email=Email("mail2@test.org"),
                last_update=datetime(2019, 10, 25, 13, 38),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
                confirm_token=Token(b"token"),
            ),
        ),
    )
    def test_roundtrip(self, instance, tiny_db_storage):
        tiny_db_storage.upsert(instance)
        assert tiny_db_storage.find(instance.email) == instance

    def test_drop_old_unconfirmed(self, tiny_db_storage):
        reference_datetime = datetime(2019, 10, 25, 13, 18)
        fresh = (
            Registration(
                email=Email("mail1@test.org"),
                last_update=reference_datetime - timedelta(days=1),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
                confirm_token=Token(b"token"),
            ),
            Registration(
                email=Email("mail2@test.org"),
                last_update=reference_datetime - timedelta(days=3),
                state=State.subscribed,
            ),
            Registration(
                email=Email("mail3@test.org"),
                last_update=reference_datetime - timedelta(days=3),
                state=State.pending_unsubscribe,
                confirm_action=Action.unsubscribe,
                confirm_token=Token(b"token"),
            ),
        )
        old = (
            Registration(
                email=Email("mail4@test.org"),
                last_update=reference_datetime - timedelta(days=3),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
                confirm_token=Token(b"token"),
            ),
        )

        for registration in fresh + old:
            tiny_db_storage.upsert(registration)

        tiny_db_storage.drop_old_unconfirmed(
            drop_before=reference_datetime - timedelta(days=2)
        )

        assert tuple(sorted(tiny_db_storage.all(), key=lambda r: r.email)) == fresh

    def test_get_unset_last_seen_storage(self, tiny_db_storage):
        assert tiny_db_storage.get_last_seen() is None

    def test_last_seen_storage(self, tiny_db_storage):
        now = datetime.now(tz=timezone(timedelta(hours=1)))
        tiny_db_storage.set_last_seen(now)
        assert tiny_db_storage.get_last_seen() == now

    def test_last_seen_storage_with_legacy_timezone_unaware_date(
        self, tiny_db, tiny_db_storage
    ):
        now = datetime.now(tz=timezone.utc)
        tiny_db.insert(
            {"key": "last_seen", "value": now.replace(tzinfo=None).isoformat()}
        )
        assert tiny_db_storage.get_last_seen() == now

    def test_get_all_active_subscribers(self, tiny_db_storage):
        active = (
            Registration(
                email=Email("mail1@test.org"),
                last_update=datetime.utcnow(),
                state=State.subscribed,
            ),
            Registration(
                email=Email("mail2@test.org"),
                last_update=datetime.now(),
                state=State.pending_unsubscribe,
                confirm_action=Action.unsubscribe,
                confirm_token=Token(b"token"),
            ),
        )
        inactive = (
            Registration(
                email=Email("mail3@test.org"),
                last_update=datetime.now(),
                state=State.pending_subscribe,
                confirm_action=Action.subscribe,
                confirm_token=Token(b"token"),
            ),
        )

        for registration in active + inactive:
            tiny_db_storage.upsert(registration)

        result = tiny_db_storage.get_all_active_subscribers()

        assert tuple(sorted(result, key=lambda r: r.email)) == active
