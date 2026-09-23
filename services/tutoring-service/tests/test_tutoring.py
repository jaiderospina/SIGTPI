import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "tutoring-service"

@pytest.mark.asyncio
async def test_list_assignments_unauthenticated(client):
    r = await client.get("/api/v1/assignments")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_create_assignment_unauthenticated(client):
    r = await client.post("/api/v1/assignments", json={
        "student_id": str(uuid4()), "tutor_id": str(uuid4()),
        "program_id": str(uuid4()), "research_area": "Ciberseguridad"
    })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_workload_unauthenticated(client):
    r = await client.get(f"/api/v1/assignments/tutor/{uuid4()}/workload")
    assert r.status_code == 401
