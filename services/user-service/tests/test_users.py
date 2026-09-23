"""Tests para user-service."""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    assert r.json()["service"] == "user-service"


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_list_users_unauthenticated(client: AsyncClient):
    r = await client.get("/api/v1/users")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_rbac_check_unauthenticated(client: AsyncClient):
    r = await client.post("/api/v1/roles/check", json={
        "user_id": str(uuid4()),
        "required_roles": ["ADM"],
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_assign_role_unauthenticated(client: AsyncClient):
    r = await client.post("/api/v1/roles/assign", json={
        "user_id": str(uuid4()),
        "role_code": "EST",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_user_unauthenticated(client: AsyncClient):
    r = await client.post("/api/v1/users", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "initial_role": "EST",
    })
    assert r.status_code == 401
