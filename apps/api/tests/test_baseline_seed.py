import pytest
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.db import BASELINE_ROOM_NUMBER, ensure_baseline_facility
from app.models.facility import Facility, Room, Tank
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.seed import seed

DB_NAME = "acare-mvp-baseline-seed-test"


@pytest.fixture
async def scratch_db(monkeypatch):
    """Point Beanie at a throwaway database so seeding cannot touch dev data.

    seed() calls init_db(), which re-initialises Beanie from settings, so the
    database name has to be overridden there too or seed() silently runs
    against (and edits) the real dev database.
    """
    monkeypatch.setattr(settings, "MONGODB_DB_NAME", DB_NAME)
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await client.drop_database(DB_NAME)
    await init_beanie(database=client[DB_NAME], document_models=[Facility, Room, Tank, User])
    yield
    await client.drop_database(DB_NAME)
    client.close()


@pytest.mark.asyncio
async def test_seeding_is_idempotent(scratch_db):
    _, first = await ensure_baseline_facility()
    _, second = await ensure_baseline_facility()

    assert first.id == second.id
    assert await Room.find_all().count() == 1
    assert await Tank.find_all().count() == 14


@pytest.mark.asyncio
async def test_renamed_room_is_not_seeded_twice(scratch_db):
    """A renamed pilot room must not read as a missing room.

    The room was renamed from "301" to "1" in production. Looking it up by
    number made the next boot seed a second room plus a duplicate set of 14
    tanks, which is the bug this guards.
    """
    _, room = await ensure_baseline_facility()
    room.room_number = "301"
    await room.save()

    _, found = await ensure_baseline_facility()

    assert found.id == room.id, "renamed room should be reused, not duplicated"
    assert await Room.find_all().count() == 1
    assert await Tank.find_all().count() == 14


@pytest.mark.asyncio
async def test_retired_tanks_are_not_resurrected(scratch_db):
    _, room = await ensure_baseline_facility()
    tank = await Tank.find_one({"room_id": str(room.id), "tank_number": "7"})
    tank.deleted = True
    await tank.save()

    await ensure_baseline_facility()

    assert await Tank.find_all().count() == 14
    still_deleted = await Tank.get(tank.id)
    assert still_deleted.deleted is True


@pytest.mark.asyncio
async def test_soft_deleted_room_is_replaced(scratch_db):
    _, room = await ensure_baseline_facility()
    room.deleted = True
    await room.save()

    _, fresh = await ensure_baseline_facility()

    assert fresh.id != room.id
    assert fresh.room_number == BASELINE_ROOM_NUMBER
    assert await Tank.find({"room_id": str(fresh.id)}).count() == 14


@pytest.mark.asyncio
async def test_seed_does_not_overwrite_existing_superadmin_password(scratch_db):
    await seed()
    admin = await User.find_one({"email": "superadmin@uwindsor.ca"})
    assert admin is not None
    assert verify_password("ChangeMe123!", admin.password_hash)

    # Change superadmin password to custom
    admin.password_hash = hash_password("MyNewCustomPassword123!")
    await admin.save()

    # Re-run seed (simulating a new deploy)
    await seed()

    # Verify password was NOT overwritten
    updated_admin = await User.find_one({"email": "superadmin@uwindsor.ca"})
    assert verify_password("MyNewCustomPassword123!", updated_admin.password_hash)
    assert not verify_password("ChangeMe123!", updated_admin.password_hash)

