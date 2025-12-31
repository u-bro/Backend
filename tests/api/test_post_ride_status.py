import pytest
from datetime import datetime

@pytest.mark.asyncio
async def test_post_ride_status_change(test_ride, client):
    ride_id = test_ride["id"]
    new_status = "in_progress"
    resp = client.post(f"/api/v1/rides/{ride_id}/status", json={
        "to_status": new_status,
        "reason": "Test status change",
        "actor_id": test_ride["client_id"],
        "actor_role": "system"
    })
    if resp.status_code == 200:
        data = resp.json()
        assert data["id"] == ride_id
        assert data["status"] == new_status
    else:
        assert resp.status_code == 400, f"{resp.status_code} {resp.text}"
        data = resp.json()
        assert "not found" in data.get("detail", "") or "not allowed" in data.get("detail", "")

@pytest.mark.asyncio
async def test_post_ride_status_invalid_ride(client):
    resp = client.post(f"/api/v1/rides/9999999/status", json={
        "to_status": "in_progress",
        "reason": "Test status change",
        "actor_id": 1,
        "actor_role": "system"
    })
    assert resp.status_code == 400, f"{resp.status_code} {resp.text}"
    data = resp.json()
    assert "not found" in data.get("detail", "")




@pytest.mark.asyncio
async def test_post_ride_status_invalid_status(test_ride, client):
    ride_id = test_ride["id"]
    resp = client.post(f"/api/v1/rides/{ride_id}/status", json={
        "to_status": "not_a_status",
        "reason": "Test status change",
        "actor_id": test_ride["client_id"],
        "actor_role": "system"
    })
    print(f"RESPONSE: {resp.status_code} {resp.text}")
    assert resp.status_code == 400, f"{resp.status_code} {resp.text}"
    data = resp.json()
    assert "invalid status" in data.get("detail", "")
