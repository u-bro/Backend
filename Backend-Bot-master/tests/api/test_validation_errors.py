import pytest

@pytest.mark.asyncio
async def test_validation_error_user_create(client):
    resp = client.post("/api/v1/users/abc", json={"telegram_id": "abc", "first_name": "", "username": ""})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_validation_error_ride_create(client):
    resp = client.post("/api/v1/rides", json={"client_id": None, "pickup_address": "", "pickup_lat": "abc"})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_validation_error_chat_send(test_ride, client):
    ride_id = test_ride["id"]
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": 1}, json={"text": ""})
    assert resp.status_code == 422 or resp.status_code == 400

@pytest.mark.asyncio
async def test_validation_error_matching_register(client):
    resp = client.post("/api/v1/matching/driver/register", json={"user_id": "abc"})
    assert resp.status_code == 422
