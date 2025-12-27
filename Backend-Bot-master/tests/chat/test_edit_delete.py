import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_delete_message_soft(test_ride, test_user, client):
    """Автор может мягко удалить своё сообщение, оно исчезает из истории"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем сообщение
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": "Удалить меня"})
    msg_id = resp.json()["id"]
    # Удаляем
    resp2 = client.delete(f"/api/v1/chat-messages/{msg_id}")
    assert resp2.status_code == 200
    # Проверяем, что в истории нет
    resp3 = client.get(f"/api/v1/chat/{ride_id}/history")
    data = resp3.json()
    assert all(m["id"] != msg_id for m in data["messages"])

@pytest.mark.asyncio
async def test_edit_message(test_ride, test_user, client):
    """Автор может редактировать своё сообщение, текст меняется в истории"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем сообщение
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": "Редактировать меня"})
    msg_id = resp.json()["id"]
    # Редактируем
    new_text = "Я отредактирован"
    resp2 = client.put(f"/api/v1/chat-messages/{msg_id}", json={"text": new_text})
    assert resp2.status_code == 200
    # Проверяем, что текст изменился
    resp3 = client.get(f"/api/v1/chat/{ride_id}/history")
    data = resp3.json()
    assert any(m["id"] == msg_id and m["text"] == new_text for m in data["messages"])

@pytest.mark.asyncio
async def test_delete_edit_foreign_message_forbidden(test_ride, test_user, client):
    """Чужое сообщение нельзя удалить или редактировать"""
    ride_id = test_ride["id"]
    sender_id = test_user["id"]
    # Отправляем сообщение от первого пользователя
    resp = client.post(f"/api/v1/chat/{ride_id}/send", params={"sender_id": sender_id}, json={"text": "Чужое"})
    msg_id = resp.json()["id"]
    # Создаём второго пользователя
    resp2 = client.post(f"/api/v1/users/{sender_id+1}", json={"telegram_id": sender_id+1, "first_name": "Другой", "username": f"other_{sender_id+1}"})
    other_id = resp2.json()["id"]
    # Пытаемся удалить чужое сообщение
    resp3 = client.delete(f"/api/v1/chat-messages/{msg_id}", params={"user_id": other_id})
    assert resp3.status_code in (403, 404)
    # Пытаемся редактировать чужое сообщение
    resp4 = client.put(f"/api/v1/chat-messages/{msg_id}", json={"text": "hack"}, params={"user_id": other_id})
    assert resp4.status_code in (403, 404)
