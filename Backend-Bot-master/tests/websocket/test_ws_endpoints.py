import pytest

@pytest.mark.asyncio
async def test_ws_stats(client):
    resp = client.get("/ws/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "online_users" in data
    assert "total_connections" in data
    assert "active_rides" in data

@pytest.mark.asyncio
async def test_ws_notify(client, test_user):
    user_id = test_user["id"]
    resp = client.post(f"/ws/notify/{user_id}", json={"message": "test notify"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_ws_broadcast(client):
    resp = client.post("/ws/broadcast", json={"message": "broadcast msg"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_ws_driver_location(client, test_user):
    user_id = test_user["id"]
    resp = client.post(f"/ws/driver/{user_id}/location", json={"latitude": 50.45, "longitude": 30.52})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_ws_driver_status(client, test_user):
    user_id = test_user["id"]
    resp = client.post(f"/ws/driver/{user_id}/status", json={"status": "online"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_ws_driver_state(client, test_user):
    user_id = test_user["id"]
    resp = client.get(f"/ws/driver/{user_id}/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data

@pytest.mark.asyncio
async def test_ws_drivers_stats(client):
    resp = client.get("/ws/drivers/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "ws_connections" in data
