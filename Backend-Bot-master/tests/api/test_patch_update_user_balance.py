
import pytest

@pytest.mark.asyncio
async def test_patch_update_user_balance(test_user, client):
    user_id = test_user["id"]
    resp = client.patch(f"/api/v1/users/update_user_balance/{user_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "balance_increase" in data
    assert "new_balance" in data

@pytest.mark.asyncio
async def test_patch_update_user_balance_invalid_user(client):
    resp = client.patch(f"/api/v1/users/update_user_balance/9999999")
    assert resp.status_code == 400, f"{resp.status_code} {resp.text}"
    data = resp.json()
    assert "User not found" in data.get("detail", "")
