import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_send_message_and_history(test_ride, test_user, client):
    """Отправка сообщения сохраняет его и возвращает в истории"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    text = "Тестовое сообщение"
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": text})
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["text"] == text
    # Проверяем, что появилось в истории
    resp2 = client.get(f"/api/v1/chat/{ride_id}/history")
    data = resp2.json()
    assert any(m["text"] == text for m in data["messages"])

@pytest.mark.asyncio
async def test_send_message_moderation(test_ride, test_user, client):
    """Сообщение с матом цензурируется и проходит модерацию"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    text = "бля тест"
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": text})
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["is_moderated"] is True
    assert "*" in msg["text"] or msg["text"] != text

@pytest.mark.asyncio
async def test_send_message_rate_limit(test_ride, test_user, client):
    """Rate limit срабатывает при спаме"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем много сообщений подряд
    for _ in range(11):
        resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": "msg"})
    # Следующее должно быть заблокировано
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": "msg"})
    assert resp.status_code in (400, 429)
    data = resp.json()
    assert "rate limit" in data.get("message", "") or "rate_limit" in data.get("code", "")
