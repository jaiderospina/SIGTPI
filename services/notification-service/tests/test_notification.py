import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_my_notifications_unauthenticated(client):
    r = await client.get("/api/v1/notifications/my")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_unread_count_unauthenticated(client):
    r = await client.get("/api/v1/notifications/my/unread-count")
    assert r.status_code == 401
