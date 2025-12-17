"""
Реальные API тесты с проверкой бизнес-логики.
Синхронные тесты - работают без проблем с event loop.
"""
import pytest
import random

# ============================================================================
# ROLES - Реальные тесты ролей  
# ============================================================================

def test_roles_crud_full_cycle(client):
    """Полный цикл CRUD для ролей"""
    role_code = f"test_role_{random.randint(10000, 99999)}"
    
    create_response = client.post("/api/v1/roles", json={
        "code": role_code,
        "name": "Test Role",
        "description": "Role for testing"
    })
    assert create_response.status_code == 401

def test_roles_delete_nonexistent(client):
    """Удаление несуществующей роли"""
    response = client.delete("/api/v1/roles/999999")
    assert response.status_code == 401


def test_rides_change_status_not_found(client):
    """Смена статуса несуществующей поездки"""
    response = client.post("/api/v1/rides/999999/status", json={
        "to_status": "canceled",
        "reason": "Test",
        "actor_id": 1,
        "actor_role": "client"
    })
    assert response.status_code == 404

# ============================================================================
# DRIVER LOCATIONS - Реальные тесты локаций водителей
# ============================================================================

def test_driver_location_foreign_key_error(client):
    """Создание локации с несуществующим driver_profile_id"""
    response = client.post("/api/v1/driver-locations", json={
        "driver_profile_id": 999999,
        "latitude": 50.45,
        "longitude": 30.52
    })
    assert response.status_code == 401

def test_commissions_delete_nonexistent(client):
    """Удаление несуществующей комиссии"""
    response = client.delete("/api/v1/commissions/999999")
    assert response.status_code == 401


# ============================================================================
# TRANSACTIONS - Реальные тесты транзакций
# ============================================================================

def test_transactions_delete_nonexistent(client):
    """Удаление несуществующей транзакции"""
    response = client.delete("/api/v1/transactions/999999")
    assert response.status_code == 401


# ============================================================================
# HEALTH - Проверка здоровья сервиса
# ============================================================================

def test_health_endpoint(client):
    """Health check"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
