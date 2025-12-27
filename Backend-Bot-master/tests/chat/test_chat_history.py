import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_history_empty(test_ride, client):
    """История чата пуста, если сообщений не было"""
    ride_id = test_ride["id"]
    resp = client.get(f"/api/v1/chat/{ride_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ride_id"] == ride_id
    assert data["messages"] == []
    assert data["count"] == 0
    assert data["has_more"] is False

@pytest.mark.asyncio
async def test_chat_history_with_messages(test_ride, test_user, client):
    """История чата возвращает отправленные сообщения"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем 2 сообщения
    for text in ("Привет", "Как дела?"):
        resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": text})
        assert resp.status_code == 200
    # Получаем историю
    resp = client.get(f"/api/v1/chat/{ride_id}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    texts = [m["text"] for m in data["messages"]]
    assert "Привет" in texts and "Как дела?" in texts
    assert data["has_more"] is False

@pytest.mark.asyncio
async def test_chat_history_pagination(test_ride, test_user, client):
    """Пагинация истории чата работает корректно"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем 3 сообщения
    ids = []
    for text in ("msg1", "msg2", "msg3"):
        resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": text})
        ids.append(resp.json()["id"])
    # Получаем только 2 последних
    resp = client.get(f"/api/v1/chat/{ride_id}/history", params={"limit": 2})
    data = resp.json()
    assert data["count"] == 2
    assert data["has_more"] is True
    # Получаем предыдущие через before_id
    before_id = data["messages"][0]["id"]
    resp2 = client.get(f"/api/v1/chat/{ride_id}/history", params={"before_id": before_id, "limit": 2})
    data2 = resp2.json()
    assert data2["count"] >= 1
    all_ids = [m["id"] for m in data["messages"] + data2["messages"]]
    for i in ids:
        assert i in all_ids
