import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "academic-registry"

@pytest.mark.asyncio
async def test_list_programs_unauthenticated(client):
    r = await client.get("/api/v1/programs")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_list_enrollments_unauthenticated(client):
    r = await client.get("/api/v1/enrollments")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_check_prerequisites_unauthenticated(client):
    r = await client.post("/api/v1/enrollments/prerequisites/check", json={
        "student_id": str(uuid4()), "program_id": str(uuid4()), "check_type": "ti_start"
    })
    assert r.status_code == 401
