import pytest

@pytest.mark.asyncio
async def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok" or "healthy" in data.get("status", "")
