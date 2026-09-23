import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_issue_cert_unauthenticated(client):
    r = await client.post("/api/v1/pki/certificates", json={
        "user_id": str(uuid4()), "common_name": "Test User",
        "email": "test@sigtpi.local"
    })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_sign_unauthenticated(client):
    r = await client.post("/api/v1/pki/sign", json={
        "document_id": str(uuid4()), "document_type": "minutes",
        "document_hash": "a" * 64, "signer_id": str(uuid4())
    })
    assert r.status_code == 401
