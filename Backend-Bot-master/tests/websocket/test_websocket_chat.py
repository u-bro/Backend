import pytest
import asyncio
import websockets
import json

def test_get_websocket_stats(client):
    resp = client.get("/api/v1/ws/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "online_users" in data
    assert "total_connections" in data
    assert "active_rides" in data

WS_URL = "ws://localhost:5000/api/v1/chat/ws/{ride_id}?user_id={user_id}"

@pytest.mark.asyncio
async def test_websocket_chat_basic(test_ride, test_user):
    ride_id = test_ride["id"]
    user_id = test_user["id"]
    url = WS_URL.format(ride_id=ride_id, user_id=user_id)
    async with websockets.connect(url) as ws:
        msg = await ws.recv()
        data = json.loads(msg)
        assert data["type"] == "connected"
        await ws.send(json.dumps({"type": "message", "text": "ws test"}))
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data["type"] == "new_message":
                assert data["message"]["text"] == "ws test"
                break

@pytest.mark.asyncio
async def test_websocket_user_joined_left(test_ride, test_user):
    ride_id = test_ride["id"]
    user1 = test_user["id"]
    user2_resp = await asyncio.to_thread(lambda: user1+1)
    user2 = user2_resp
    url1 = WS_URL.format(ride_id=ride_id, user_id=user1)
    url2 = WS_URL.format(ride_id=ride_id, user_id=user2)
    async with websockets.connect(url1) as ws1:
        await ws1.recv() 
        async with websockets.connect(url2) as ws2:
            await ws2.recv()  
            while True:
                msg = await ws1.recv()
                data = json.loads(msg)
                if data["type"] == "user_joined" and data["user_id"] == user2:
                    break
        while True:
            msg = await ws1.recv()
            data = json.loads(msg)
            if data["type"] == "user_left" and data["user_id"] == user2:
                break

@pytest.mark.asyncio
async def test_websocket_typing_event(test_ride, test_user):
    ride_id = test_ride["id"]
    user_id = test_user["id"]
    url = WS_URL.format(ride_id=ride_id, user_id=user_id)
    async with websockets.connect(url) as ws:
        await ws.recv()  
        await ws.send(json.dumps({"type": "typing"}))
        await asyncio.sleep(0.1)
