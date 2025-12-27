
import pytest

@pytest.mark.asyncio
async def test_matching_driver_register(test_driver_profile, client, test_user):
    driver_profile_id = test_driver_profile["id"]
    user_id = test_user["id"]
    payload = {
        "driver_profile_id": driver_profile_id,
        "user_id": user_id,
        "classes_allowed": ["economy"],
        "rating": 5.0
    }
    resp = client.post("/api/v1/matching/driver/register", json=payload)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert "driver_profile_id" in data
    loc_resp = client.post(f"/api/v1/ws/driver/{user_id}/location", json={"latitude": 50.45, "longitude": 30.52})
    assert loc_resp.status_code in (200, 202), loc_resp.text

@pytest.mark.asyncio
async def test_matching_feed(test_driver_profile, client, test_user):
    driver_profile_id = test_driver_profile["id"]
    user_id = test_user["id"]
    client.post("/api/v1/matching/driver/register", json={
        "driver_profile_id": driver_profile_id,
        "user_id": user_id,
        "classes_allowed": ["economy"],
        "rating": 5.0
    })
    client.post(f"/api/v1/ws/driver/{user_id}/location", json={"latitude": 50.45, "longitude": 30.52})
    resp = client.get(f"/api/v1/matching/feed/{driver_profile_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "rides" in data

@pytest.mark.asyncio
async def test_matching_accept(test_ride, test_driver_profile, client, test_user):
    ride_id = test_ride["id"]
    driver_profile_id = test_driver_profile["id"]
    user_id = test_user["id"]
    client.post("/api/v1/matching/driver/register", json={
        "driver_profile_id": driver_profile_id,
        "user_id": user_id,
        "classes_allowed": ["economy"],
        "rating": 5.0
    })
    client.post(f"/api/v1/ws/driver/{user_id}/location", json={"latitude": 50.45, "longitude": 30.52})
    payload = {"driver_profile_id": driver_profile_id, "user_id": user_id}
    resp = client.post(f"/api/v1/matching/accept/{ride_id}", json=payload)
    assert resp.status_code in (200, 201, 409), resp.text

@pytest.mark.asyncio
async def test_matching_find_drivers(test_ride, client):
    ride_id = test_ride["id"]
    resp_ride = client.get(f"/api/v1/rides/{ride_id}")
    ride = resp_ride.json()
    payload = {
        "ride_id": ride_id,
        "ride_class": "economy",
        "pickup_lat": ride.get("pickup_lat", 50.45),
        "pickup_lng": ride.get("pickup_lng", 30.52),
        "search_radius_km": 5.0
    }
    resp = client.post("/api/v1/matching/find-drivers", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "drivers" in data

@pytest.mark.asyncio
async def test_matching_stats(client):
    resp = client.get("/api/v1/matching/stats")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "config" in data and "tracker_stats" in data
