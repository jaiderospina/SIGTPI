import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "session-service"

@pytest.mark.asyncio
async def test_list_sessions_unauthenticated(client):
    r = await client.get("/api/v1/sessions")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_create_session_unauthenticated(client):
    r = await client.post("/api/v1/sessions", json={
        "ti_id": str(uuid4()), "tutor_id": str(uuid4()), "student_id": str(uuid4()),
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "modality": "virtual",
    })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_minutes_unauthenticated(client):
    r = await client.post("/api/v1/sessions/minutes", json={
        "session_id": str(uuid4()), "topics_covered": "Test topics"
    })
    assert r.status_code == 401
