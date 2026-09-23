import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_list_rubrics_unauthenticated(client):
    r = await client.get("/api/v1/evaluations/rubrics")
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_submit_score_unauthenticated(client):
    r = await client.post("/api/v1/evaluations/scores", json={
        "evaluation_id": str(uuid4()), "scores": {"c1": 4.0}
    })
    assert r.status_code == 401
