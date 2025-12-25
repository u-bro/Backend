import json
import websocket
import threading
import time

# Simple WebSocket access control test using a blocking client.
# Assumes WS endpoint: ws://localhost:5000/api/v1/ws/{user_id}

WS_BASE = "ws://localhost:5000/api/v1/ws"


def open_ws(user_id):
    ws = websocket.WebSocket()
    ws.connect(f"{WS_BASE}/{user_id}")
    return ws


def send_join(ws, ride_id):
    msg = {"type": "join_ride", "ride_id": ride_id}
    ws.send(json.dumps(msg))
    # read response
    try:
        res = ws.recv()
        return json.loads(res)
    except Exception:
        return None


def test_ws_join_access_control():
    # Create a ride via HTTP to have a real ride_id
    import requests
    BASE = "http://localhost:5000/api/v1"
    cu = requests.post(f"{BASE}/users/200001", json={"telegram_id":200001, "first_name":"T", "username":"t2"})
    # create ride
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
    ride_id = ride_resp.json()["id"]

    # connect as unrelated user and try to join
    ws = open_ws(99999)
    res = send_join(ws, ride_id)
    # Expect an error/forbidden response
    assert res is None or res.get("error") or res.get("type") == "error"
    ws.close()

    # connect as client (id 2) and join
    wsc = open_ws(2)
    res2 = send_join(wsc, ride_id)
    # expecting success or ack
    assert res2 is not None
    wsc.close()
