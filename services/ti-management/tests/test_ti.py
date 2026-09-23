import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "ti-management"

@pytest.mark.asyncio
async def test_list_ti_unauthenticated(client):
    r = await client.get("/api/v1/ti")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_create_ti_unauthenticated(client):
    r = await client.post("/api/v1/ti", json={
        "assignment_id": str(uuid4()), "student_id": str(uuid4()),
        "tutor_id": str(uuid4()), "program_id": str(uuid4()),
        "title": "Análisis de Seguridad en Redes SDN",
        "knowledge_area": "Ciberseguridad y Ciberdefensa",
    })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_kpi_summary_unauthenticated(client):
    r = await client.get("/api/v1/ti/summary")
    assert r.status_code == 401
