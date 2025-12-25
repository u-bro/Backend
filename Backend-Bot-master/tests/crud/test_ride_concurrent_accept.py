import threading
import time
import requests

BASE = "http://localhost:5000/api/v1"

# This test assumes the app is running locally and accessible at BASE.
# It does not modify application code; it exercises the public HTTP API.


def accept_ride(ride_id, driver_profile_id, results, idx):
    url = f"{BASE}/rides/{ride_id}/accept"
    payload = {"driver_profile_id": driver_profile_id}
    try:
        r = requests.post(url, json=payload, timeout=10)
        results[idx] = (r.status_code, r.json() if r.content else None)
    except Exception as e:
        results[idx] = ("error", str(e))


def test_concurrent_accept_flow():
    # Create a ride and two driver profiles using the public API.
    # For robust CI this should use fixtures; here we do simple calls.
    # Create client user
    cu = requests.post(f"{BASE}/users/100001", json={"telegram_id":100001, "first_name":"T", "username":"t1"})
    assert cu.status_code in (200,201,401)

    ride_resp = requests.post(f"{BASE}/rides", json={
        "client_id": 2,
        "pickup_address": "A",
        "pickup_lat": 50.45,
        "pickup_lng": 30.52,
        "dropoff_address": "B",
        "dropoff_lat": 50.46,
        "dropoff_lng": 30.53,
        "expected_fare": 10.0,
        "expected_fare_snapshot": {}
    })
    assert ride_resp.status_code == 201
    ride = ride_resp.json()
    ride_id = ride["id"]

    # create two driver profiles
    dp1 = requests.post(f"{BASE}/users/100002", json={"telegram_id":100002, "first_name":"D1", "username":"d1"})
    dp2 = requests.post(f"{BASE}/users/100003", json={"telegram_id":100003, "first_name":"D2", "username":"d2"})
    # create driver-profiles
    r1 = requests.post(f"{BASE}/driver-profiles", json={"user_id": dp1.json().get('id', 3)})
    r2 = requests.post(f"{BASE}/driver-profiles", json={"user_id": dp2.json().get('id', 4)})
    assert r1.status_code == 201
    assert r2.status_code == 201
    dp1_id = r1.json()["id"]
    dp2_id = r2.json()["id"]

    results = [None, None]
    t1 = threading.Thread(target=accept_ride, args=(ride_id, dp1_id, results, 0))
    t2 = threading.Thread(target=accept_ride, args=(ride_id, dp2_id, results, 1))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one of them should succeed with 200 and the other should be 409 or similar
    statuses = [r[0] for r in results]
    assert 200 in statuses
    assert any(s in (409, 400, 422) or s == "error" for s in statuses if s != 200)

