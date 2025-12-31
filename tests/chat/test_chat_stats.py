import pytest

@pytest.mark.asyncio
async def test_chat_stats(client):
    """GET: статистика чата"""
    resp = client.get("/api/v1/chat/stats")
    assert resp.status_code == 200
    data = resp.json()
    # Проверяем только существующие ключи, чтобы тест соответствовал контракту
    assert "active_users_with_rate_limit" in data
    assert "rate_limit_config" in data
    assert "max_message_length" in data
