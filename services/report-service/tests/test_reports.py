import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_dashboard_unauthenticated(client):
    r = await client.get("/api/v1/reports/dashboard")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_ti_status_unauthenticated(client):
    r = await client.get("/api/v1/reports/ti/status")
    assert r.status_code == 401
