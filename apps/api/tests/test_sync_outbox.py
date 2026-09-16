import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import init_db


@pytest.mark.asyncio
async def test_sync_outbox_unauthorized():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/sync/outbox", json={"items": []})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sync_outbox_success():
    await init_db()
    key1 = f"uuid-test-wq-{uuid.uuid4()}"
    key2 = f"uuid-test-inc-{uuid.uuid4()}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", json={"email": "superadmin@uwindsor.ca", "password": "ChangeMe123!"})
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "items": [
                {
                    "idempotency_key": key1,
                    "entity_type": "water_quality_log",
                    "payload": {
                        "tank_id": "tank_101",
                        "ph": 7.4,
                        "temperature": 26.5,
                        "comments": "Offline logged reading",
                    },
                },
                {
                    "idempotency_key": key2,
                    "entity_type": "incident_report",
                    "payload": {
                        "tank_id": "tank_102",
                        "problem_description": "Offline captured incident description.",
                        "vet_contacted": False,
                    },
                },
            ]
        }
        response = await ac.post("/sync/outbox", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["idempotency_key"] == key1
        assert data[0]["status"] == "synced"
        assert data[1]["idempotency_key"] == key2
        assert data[1]["status"] == "synced"

        # Idempotent retry test
        retry_res = await ac.post("/sync/outbox", json=payload, headers=auth_headers)
        assert retry_res.status_code == 200
        retry_data = retry_res.json()
        assert retry_data[0]["status"] == "duplicate"
        assert retry_data[1]["status"] == "duplicate"

