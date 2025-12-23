from fastapi.testclient import TestClient
import random
import pytest
import sys
sys.path.append("../app/backend")
from app.backend.main import app

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user(client):
    telegram_id = random.randint(100000, 999999)
    response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "TestUser",
        "username": f"testuser_1"
    })
    assert response.status_code == 401
    return     {
        "first_name": None,
        "last_name": None,
        "username": "asd",
        "phone": "+375295447082",
        "id": 2,
        "created_at": "2025-12-17T17:11:22.946612",
        "last_active": None,
        "is_active": None
    }

@pytest.fixture
def test_role(client):
    code = f"role_{random.randint(10000, 99999)}"
    response = client.post("/api/v1/roles", json={
        "code": code,
        "name": "Test Role"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_ride(client, test_user):
    """Создаёт тестовую поездку"""
    response = client.post("/api/v1/rides", json={
        "client_id": test_user["id"],
        "pickup_address": "Test Pickup",
        "pickup_lat": 50.45,
        "pickup_lng": 30.52,
        "dropoff_address": "Test Dropoff",
        "dropoff_lat": 50.46,
        "dropoff_lng": 30.53,
        "expected_fare": 100.0,
        "expected_fare_snapshot": {}
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_driver_profile(client):
    """Создаёт тестовый профиль водителя"""
    telegram_id = random.randint(100000, 999999)
    user_response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "TestDriver",
        "username": f"testdriver_{telegram_id}"
    })
    user_id = user_response.json()["id"]
    
    response = client.post("/api/v1/driver-profiles", json={
        "user_id": user_id
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_driver_location(client, test_driver_profile):
    """Создаёт тестовую локацию водителя"""
    response = client.post("/api/v1/driver-locations", json={
        "driver_profile_id": test_driver_profile["id"],
        "latitude": 50.45,
        "longitude": 30.52
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_driver_document(client, test_driver_profile):
    """Создаёт тестовый документ водителя"""
    response = client.post("/api/v1/driver-documents", json={
        "driver_profile_id": test_driver_profile["id"],
        "doc_type": "license",
        "file_url": "https://example.com/doc.pdf"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_commission(client):
    """Создаёт тестовую комиссию"""
    response = client.post("/api/v1/commissions", json={
        "name": f"Commission {random.randint(1000, 9999)}",
        "percentage": 15.0
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_phone_verification(client, test_user):
    """Создаёт тестовую верификацию телефона"""
    response = client.post("/api/v1/phone-verifications", json={
        "user_id": test_user["id"],
        "phone": f"+38099{random.randint(1000000, 9999999)}",
        "code": str(random.randint(100000, 999999))
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_transaction(client, test_user):
    """Создаёт тестовую транзакцию"""
    response = client.post("/api/v1/transactions", json={
        "user_id": test_user["id"],
        "is_withdraw": False,
        "amount": 100.0
    })
    assert response.status_code == 201
    return response.json()

