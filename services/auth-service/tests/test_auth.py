"""Tests for auth endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_missing_body(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_credentials(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "wrongpassword"
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 403  # No bearer token
