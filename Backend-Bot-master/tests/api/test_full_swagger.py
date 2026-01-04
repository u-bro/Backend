import pytest
import random

def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_users_list(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_users_create_and_get(client):
    telegram_id = random.randint(100000, 999999)
    response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "SwaggerTest",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == telegram_id

def test_users_update(client, test_user):
    response = client.put(f"/api/v1/users/{test_user['id']}", json={
        "id": test_user["id"],
        "telegram_id": test_user["telegram_id"],
        "first_name": "UpdatedSwagger",
        "balance": 200.0
    })
    assert response.status_code == 200

def test_users_update_nonexistent(client):
    response = client.put("/api/v1/users/999999", json={
        "id": 999999,
        "telegram_id": 999999,
        "first_name": "Ghost",
        "balance": 0.0
    })
    assert response.status_code in (404, 422)

def test_roles_list(client):
    response = client.get("/api/v1/roles")
    assert response.status_code == 401


def test_roles_create(client):
    code = f"role_{random.randint(10000, 99999)}"
    response = client.post("/api/v1/roles", json={
        "code": code,
        "name": code
    })
    assert response.status_code == 401


def test_roles_update(client, test_role):
    response = client.put(f"/api/v1/roles/{test_role['id']}", json={
        "name": "UpdatedRole"
    })
    assert response.status_code == 200


def test_roles_delete(client, test_role):
    response = client.delete(f"/api/v1/roles/{test_role['id']}")
    assert response.status_code == 200


def test_roles_delete_nonexistent(client):
    response = client.delete("/api/v1/roles/999999")
    assert response.status_code == 401



def test_rides_list(client):
    response = client.get("/api/v1/rides")
    assert response.status_code == 401


def test_rides_create(client, test_user):
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

def test_rides_get_by_id(client, test_ride):
    response = client.get(f"/api/v1/rides/{test_ride['id']}")
    assert response.status_code == 200


def test_rides_get_nonexistent(client):
    response = client.get("/api/v1/rides/999999")
    assert response.status_code == 401


def test_rides_update(client, test_ride):
    response = client.put(f"/api/v1/rides/{test_ride['id']}", json={
        "pickup_address": "Updated Pickup"
    })
    assert response.status_code == 200


def test_rides_change_status(client, test_ride):
    ride_id = test_ride["id"]
    get_resp = client.get(f"/api/v1/rides/{ride_id}")
    if get_resp.status_code == 200:
        ride = get_resp.json()
        if ride["status"] not in ("requested", "driver_assigned", "accepted"):
            client.put(f"/api/v1/rides/{ride_id}", json={"status": "requested"})

    response = client.post(f"/api/v1/rides/{ride_id}/status", json={
        "to_status": "canceled",
        "reason": "Test cancel",
        "actor_id": test_ride["client_id"],
        "actor_role": "client"
    })
    assert response.status_code == 200, f"{response.status_code} {response.text}"


def test_rides_change_status_nonexistent(client):
    response = client.post("/api/v1/rides/999999/status", json={
        "to_status": "canceled",
        "reason": "Test",
        "actor_id": 1,
        "actor_role": "client"
    })
    assert response.status_code == 404


def test_rides_count(client):
    response = client.get("/api/v1/rides/count")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, int)


def test_driver_profiles_list(client):
    response = client.get("/api/v1/driver-profiles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_driver_profiles_create(client):
    telegram_id = random.randint(100000, 999999)
    user_response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "NewDriverProfile",
    })
    user_id = user_response.json()["id"]
    
    response = client.post("/api/v1/driver-profiles", json={
        "user_id": user_id
    })
    assert response.status_code == 201


def test_driver_profiles_get_by_id(client, test_driver_profile):
    response = client.get(f"/api/v1/driver-profiles/{test_driver_profile['id']}")
    assert response.status_code == 200


def test_driver_profiles_get_nonexistent(client):
    response = client.get("/api/v1/driver-profiles/999999")
    assert response.status_code == 401


def test_driver_profiles_update(client, test_driver_profile):
    response = client.put(f"/api/v1/driver-profiles/{test_driver_profile['id']}", json={
        "first_name": "UpdatedDriver"
    })
    assert response.status_code == 200


def test_driver_profiles_delete(client, test_driver_profile):
    response = client.delete(f"/api/v1/driver-profiles/{test_driver_profile['id']}")
    assert response.status_code == 200


def test_driver_profiles_delete_nonexistent(client):
    response = client.delete("/api/v1/driver-profiles/999999")
    assert response.status_code == 404


def test_driver_profiles_duplicate_user(client):
    telegram_id = random.randint(100000, 999999)
    user_response = client.post(f"/api/v1/users/{telegram_id}", json={
        "telegram_id": telegram_id,
        "first_name": "DuplicateDriver",
    })
    user_id = user_response.json()["id"]
    first = client.post("/api/v1/driver-profiles", json={"user_id": user_id})
    assert first.status_code == 201
    second = client.post("/api/v1/driver-profiles", json={"user_id": user_id})
    assert second.status_code == 409


def test_driver_locations_list(client):
    response = client.get("/api/v1/driver-locations")
    assert response.status_code == 401


def test_driver_locations_create(client, test_driver_profile):
    response = client.post("/api/v1/driver-locations", json={
        "driver_profile_id": test_driver_profile["id"],
        "latitude": 50.45,
        "longitude": 30.52
    })
    assert response.status_code == 201


def test_driver_locations_create_invalid_profile(client):
    response = client.post("/api/v1/driver-locations", json={
        "driver_profile_id": 999999,
        "latitude": 50.45,
        "longitude": 30.52
    })
    assert response.status_code == 401


def test_driver_locations_get_by_id(client, test_driver_location):
    response = client.get(f"/api/v1/driver-locations/{test_driver_location['id']}")
    assert response.status_code == 200


def test_driver_locations_get_nonexistent(client):
    response = client.get("/api/v1/driver-locations/999999")
    assert response.status_code == 401


def test_driver_locations_delete(client, test_driver_location):
    response = client.delete(f"/api/v1/driver-locations/{test_driver_location['id']}")
    assert response.status_code == 200


def test_driver_locations_delete_nonexistent(client):
    response = client.delete("/api/v1/driver-locations/999999")
    assert response.status_code == 401


def test_driver_documents_list(client):
    response = client.get("/api/v1/driver-documents")
    assert response.status_code == 401


def test_driver_documents_create(client, test_driver_profile):
    response = client.post("/api/v1/driver-documents", json={
        "driver_profile_id": test_driver_profile["id"],
        "doc_type": "license",
        "file_url": "https://example.com/doc.pdf"
    })
    assert response.status_code == 201


def test_driver_documents_create_invalid_profile(client):
    response = client.post("/api/v1/driver-documents", json={
        "driver_profile_id": 999999,
        "doc_type": "license",
        "file_url": "https://example.com/doc.pdf"
    })
    assert response.status_code == 401


def test_driver_documents_get_by_id(client, test_driver_document):
    response = client.get(f"/api/v1/driver-documents/{test_driver_document['id']}")
    assert response.status_code == 200


def test_driver_documents_get_nonexistent(client):
    response = client.get("/api/v1/driver-documents/999999")
    assert response.status_code == 401


def test_driver_documents_delete(client, test_driver_document):
    response = client.delete(f"/api/v1/driver-documents/{test_driver_document['id']}")
    assert response.status_code == 200


def test_driver_documents_delete_nonexistent(client):
    response = client.delete("/api/v1/driver-documents/999999")
    assert response.status_code == 401

def test_commissions_list(client):
    response = client.get("/api/v1/commissions")
    assert response.status_code == 401


def test_commissions_create(client):
    response = client.post("/api/v1/commissions", json={
        "name": f"Commission {random.randint(1000, 9999)}",
        "percentage": 10.0
    })
    assert response.status_code == 401


def test_commissions_get_by_id(client, test_commission):
    response = client.get(f"/api/v1/commissions/{test_commission['id']}")
    assert response.status_code == 200


def test_commissions_get_nonexistent(client):
    response = client.get("/api/v1/commissions/999999")
    assert response.status_code == 401


def test_commissions_update(client, test_commission):
    response = client.put(f"/api/v1/commissions/{test_commission['id']}", json={
        "percentage": 20.0
    })
    assert response.status_code == 200


def test_commissions_delete(client, test_commission):
    response = client.delete(f"/api/v1/commissions/{test_commission['id']}")
    assert response.status_code == 200


def test_commissions_delete_nonexistent(client):
    response = client.delete("/api/v1/commissions/999999")
    assert response.status_code == 404
    
    
def test_phone_verifications_list(client):
    response = client.get("/api/v1/phone-verifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_phone_verifications_create(client, test_user):
    response = client.post("/api/v1/phone-verifications", json={
        "user_id": test_user["id"],
        "phone": f"+38099{random.randint(1000000, 9999999)}",
        "code": str(random.randint(100000, 999999))
    })
    assert response.status_code == 201


def test_phone_verifications_create_invalid_user(client):
    response = client.post("/api/v1/phone-verifications", json={
        "user_id": 999999,
        "phone": "+380999999999",
        "code": "123456"
    })
    assert response.status_code == 422


def test_phone_verifications_get_by_id(client, test_phone_verification):
    response = client.get(f"/api/v1/phone-verifications/{test_phone_verification['id']}")
    assert response.status_code == 200


def test_phone_verifications_get_nonexistent(client):
    response = client.get("/api/v1/phone-verifications/999999")
    assert response.status_code == 404


def test_phone_verifications_delete(client, test_phone_verification):
    response = client.delete(f"/api/v1/phone-verifications/{test_phone_verification['id']}")
    assert response.status_code == 200


def test_phone_verifications_delete_nonexistent(client):
    response = client.delete("/api/v1/phone-verifications/999999")
    assert response.status_code == 404

def test_transactions_list(client):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_transactions_create(client, test_user):
    response = client.post("/api/v1/transactions", json={
        "user_id": test_user["id"],
        "is_withdraw": False,
        "amount": 100.0
    })
    assert response.status_code == 201


def test_transactions_create_invalid_user(client):
    response = client.post("/api/v1/transactions", json={
        "user_id": 999999,
        "is_withdraw": False,
        "amount": 100.0
    })
    assert response.status_code == 401


def test_transactions_get_by_id(client, test_transaction):
    response = client.get(f"/api/v1/transactions/{test_transaction['id']}")
    assert response.status_code == 200


def test_transactions_get_nonexistent(client):
    response = client.get("/api/v1/transactions/999999")
    assert response.status_code == 422


def test_transactions_delete(client, test_transaction):
    response = client.delete(f"/api/v1/transactions/{test_transaction['id']}")
    assert response.status_code == 200


def test_transactions_delete_nonexistent(client):
    response = client.delete("/api/v1/transactions/999999")
    assert response.status_code == 404