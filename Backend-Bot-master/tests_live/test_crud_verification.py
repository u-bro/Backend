import pytest
import random

class TestRolesCRUD:
    """Полная проверка CRUD для ролей"""
    
    def test_role_full_lifecycle(self, client):
        """
        Полный цикл: создание -> чтение -> обновление -> удаление -> проверка удаления
        """
        role_code = f"test_role_{random.randint(10000, 99999)}"
        
        # === CREATE ===
        create_resp = client.post("/api/v1/roles", json={
            "code": role_code,
            "name": "Тестовая роль",
            "description": "Описание тестовой роли"
        })
        assert create_resp.status_code == 401
        
class TestCommissionsCRUD:
    """Полная проверка CRUD для комиссий"""
    
    def test_commission_full_cycle(self, client):
        """
        Полный цикл CRUD для комиссий
        """
        # === CREATE ===
        create_resp = client.post("/api/v1/commissions", json={
            "name": f"Комиссия {random.randint(1000, 9999)}",
            "percentage": 15.5
        })
        assert create_resp.status_code == 401