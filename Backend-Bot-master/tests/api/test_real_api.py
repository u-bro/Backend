import pytest
import random


def test_users_crud_full_cycle(client):
    telegram_id = random.randint(100000, 999999)
    create_response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "TestCRUD",
        "username": f"testcrud_{telegram_id}"
    })
    assert create_response.status_code == 200, f"Create user failed: {create_response.text}"
    user_data = create_response.json()
    assert user_data["telegram_id"] == telegram_id
    user_id = user_data["id"]
    get_response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "Different",
        "username": f"different_{telegram_id}"
    })
    assert get_response.status_code == 200
    same_user = get_response.json()
    assert same_user["id"] == user_id
    update_response = client.put(f"/api/v1/users/{user_id}", json={
        "id": user_id,
        "telegram_id": telegram_id,
        "first_name": "UpdatedName",
        "username": f"updated_{telegram_id}",
        "balance": 100.0
    })
    assert update_response.status_code == 200
    list_response = client.get("/api/v1/users?page=1&page_size=100")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)


def test_users_update_nonexistent(client):
    response = client.put("/api/v1/users/999999", json={
        "id": 999999,
        "telegram_id": 999999,
        "first_name": "Ghost",
        "username": "ghost",
        "balance": 0.0
    })
    assert response.status_code in (404, 422)


def test_roles_crud_full_cycle(client):
    role_code = f"test_role_{random.randint(10000, 99999)}"
    create_response = client.post("/api/v1/roles", json={
        "code": role_code,
        "name": "Test Role",
        "description": "Role for testing"
    })
    assert create_response.status_code == 201
    role = create_response.json()
    role_id = role["id"]
    get_response = client.get(f"/api/v1/roles/{role_id}")
    assert get_response.status_code == 200
    update_response = client.put(f"/api/v1/roles/{role_id}", json={
        "name": "Updated Role Name"
    })
    assert update_response.status_code == 200
    delete_response = client.delete(f"/api/v1/roles/{role_id}")
    assert delete_response.status_code == 200
    get_after_delete = client.get(f"/api/v1/roles/{role_id}")
    assert get_after_delete.status_code == 404
