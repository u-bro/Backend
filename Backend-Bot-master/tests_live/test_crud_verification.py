"""
Тесты CRUD операций с ПОЛНОЙ ВЕРИФИКАЦИЕЙ данных.
Проверяем что данные реально создаются, сохраняются в БД, 
читаются обратно, обновляются и удаляются.
"""
import pytest
import random


class TestUsersCRUD:
    """Полная проверка CRUD для пользователей"""
    
    def test_user_create_and_verify_data(self, client):
        """
        Создаём пользователя и проверяем что ВСЕ поля сохранились корректно
        """
        telegram_id = random.randint(1000000, 9999999)
        input_data = {
            "telegram_id": telegram_id,
            "first_name": "Иван",
            "username": f"ivan_petrov_{telegram_id}"
        }
        
        # 1. Создаём пользователя
        response = client.post(f"/api/v1/users/{telegram_id}", json=input_data)
        assert response.status_code == 200, f"Failed to create user: {response.text}"
        
        created_user = response.json()
        
        # 2. Проверяем что все поля вернулись правильно
        assert created_user["telegram_id"] == telegram_id, "telegram_id не совпадает"
        assert created_user["first_name"] == "Иван", "first_name не совпадает"
        assert created_user["username"] == f"ivan_petrov_{telegram_id}", "username не совпадает"
        assert "id" in created_user, "id отсутствует в ответе"
        assert created_user["id"] is not None, "id равен None"
        
        user_id = created_user["id"]
        print(f"\n✓ Пользователь создан: id={user_id}, telegram_id={telegram_id}")
        print(f"  first_name: {created_user['first_name']}")
        print(f"  username: {created_user['username']}")
        
        # 3. Получаем пользователя из БД через список и проверяем
        list_response = client.get("/api/v1/users?page=1&page_size=1000")
        assert list_response.status_code == 200
        
        users = list_response.json()
        found_user = next((u for u in users if u["id"] == user_id), None)
        
        assert found_user is not None, f"Пользователь id={user_id} не найден в БД!"
        assert found_user["telegram_id"] == telegram_id, "telegram_id в БД не совпадает"
        assert found_user["first_name"] == "Иван", "first_name в БД не совпадает"
        
        print(f"✓ Пользователь найден в БД и данные совпадают")
        
        return user_id

    def test_user_update_and_verify(self, client):
        """
        Создаём пользователя, обновляем его и проверяем что изменения сохранились
        """
        telegram_id = random.randint(1000000, 9999999)
        
        # 1. Создаём
        create_resp = client.post(f"/api/v1/users/{telegram_id}", json={
            "telegram_id": telegram_id,
            "first_name": "До обновления",
            "username": f"before_{telegram_id}"
        })
        user_id = create_resp.json()["id"]
        original_balance = create_resp.json().get("balance", 0)
        
        print(f"\n✓ Создан пользователь id={user_id}, balance={original_balance}")
        
        # 2. Обновляем данные
        update_data = {
            "id": user_id,
            "telegram_id": telegram_id,
            "first_name": "После обновления",
            "username": f"after_{telegram_id}",
            "balance": 500.50
        }
        
        update_resp = client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        
        updated_user = update_resp.json()
        
        # 3. Проверяем что данные обновились
        assert updated_user["first_name"] == "После обновления", "first_name не обновился"
        assert updated_user["username"] == f"after_{telegram_id}", "username не обновился"
        assert updated_user["balance"] == 500.50, f"balance не обновился: {updated_user['balance']}"
        
        print(f"✓ Пользователь обновлён: first_name='{updated_user['first_name']}', balance={updated_user['balance']}")
        
        # 4. Проверяем что в БД тоже обновилось (повторный запрос)
        list_resp = client.get("/api/v1/users?page=1&page_size=1000")
        users = list_resp.json()
        db_user = next((u for u in users if u["id"] == user_id), None)
        
        assert db_user is not None, "Пользователь не найден после обновления"
        assert db_user["first_name"] == "После обновления", "В БД first_name не обновился"
        assert db_user["balance"] == 500.50, "В БД balance не обновился"
        
        print(f"✓ Проверка БД: данные действительно обновлены")


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
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        
        role = create_resp.json()
        role_id = role["id"]
        
        assert role["code"] == role_code, "code не совпадает"
        assert role["name"] == "Тестовая роль", "name не совпадает"
        
        print(f"\n✓ CREATE: Роль создана id={role_id}, code='{role_code}'")
        
        # === READ ===
        get_resp = client.get(f"/api/v1/roles/{role_id}")
        assert get_resp.status_code == 200, f"Read failed: {get_resp.text}"
        
        fetched_role = get_resp.json()
        assert fetched_role["id"] == role_id, "id не совпадает при чтении"
        assert fetched_role["code"] == role_code, "code не совпадает при чтении"
        assert fetched_role["name"] == "Тестовая роль", "name не совпадает при чтении"
        
        print(f"✓ READ: Роль получена из БД: {fetched_role}")
        
        # === UPDATE ===
        update_resp = client.put(f"/api/v1/roles/{role_id}", json={
            "name": "Обновлённая роль",
            "description": "Новое описание"
        })
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        
        updated_role = update_resp.json()
        assert updated_role["name"] == "Обновлённая роль", "name не обновился"
        
        print(f"✓ UPDATE: Роль обновлена: name='{updated_role['name']}'")
        
        # Проверяем через повторное чтение
        verify_resp = client.get(f"/api/v1/roles/{role_id}")
        verify_role = verify_resp.json()
        assert verify_role["name"] == "Обновлённая роль", "В БД name не обновился"
        
        print(f"✓ VERIFY: Данные в БД обновлены")
        
        # === DELETE ===
        delete_resp = client.delete(f"/api/v1/roles/{role_id}")
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        
        print(f"✓ DELETE: Роль удалена")
        
        # === VERIFY DELETE ===
        check_resp = client.get(f"/api/v1/roles/{role_id}")
        assert check_resp.status_code == 404, f"Роль должна быть удалена, но вернулся {check_resp.status_code}"
        
        print(f"✓ VERIFY DELETE: Роль больше не существует в БД (404)")


class TestRidesCRUD:
    """Полная проверка CRUD для поездок"""
    
    def test_ride_create_and_status_change(self, client):
        """
        Создаём поездку, проверяем данные, меняем статус
        """
        # Создаём клиента для поездки
        telegram_id = random.randint(1000000, 9999999)
        user_resp = client.post(f"/api/v1/users/{telegram_id}", json={
            "telegram_id": telegram_id,
            "first_name": "Клиент",
            "username": f"client_{telegram_id}"
        })
        client_id = user_resp.json()["id"]
        
        # === CREATE RIDE ===
        ride_data = {
            "client_id": client_id,
            "pickup_address": "ул. Пушкина, д. 10",
            "pickup_lat": 50.4501,
            "pickup_lng": 30.5234,
            "dropoff_address": "пр. Шевченко, д. 25",
            "dropoff_lat": 50.4600,
            "dropoff_lng": 30.5300,
            "expected_fare": 150.00,
            "expected_fare_snapshot": {"base": 50, "per_km": 10, "distance_km": 10}
        }
        
        create_resp = client.post("/api/v1/rides", json=ride_data)
        assert create_resp.status_code == 201, f"Create ride failed: {create_resp.text}"
        
        ride = create_resp.json()
        ride_id = ride["id"]
        
        # Проверяем все поля
        assert ride["client_id"] == client_id, "client_id не совпадает"
        assert ride["pickup_address"] == "ул. Пушкина, д. 10", "pickup_address не совпадает"
        assert ride["dropoff_address"] == "пр. Шевченко, д. 25", "dropoff_address не совпадает"
        assert ride["expected_fare"] == 150.00, "expected_fare не совпадает"
        assert ride["status"] == "requested", f"Начальный статус должен быть 'requested', получили '{ride['status']}'"
        
        print(f"\n✓ CREATE: Поездка создана id={ride_id}, status='{ride['status']}'")
        print(f"  pickup: {ride['pickup_address']}")
        print(f"  dropoff: {ride['dropoff_address']}")
        print(f"  fare: {ride['expected_fare']}")
        
        # === READ ===
        get_resp = client.get(f"/api/v1/rides/{ride_id}")
        assert get_resp.status_code == 200
        
        fetched_ride = get_resp.json()
        assert fetched_ride["id"] == ride_id, "id не совпадает"
        assert fetched_ride["pickup_address"] == "ул. Пушкина, д. 10", "pickup_address в БД не совпадает"
        
        print(f"✓ READ: Поездка получена из БД")
        
        # === CHANGE STATUS ===
        status_resp = client.post(f"/api/v1/rides/{ride_id}/status", json={
            "to_status": "canceled",
            "reason": "Клиент передумал",
            "actor_id": client_id,
            "actor_role": "client"
        })
        assert status_resp.status_code == 200, f"Status change failed: {status_resp.text}"
        
        updated_ride = status_resp.json()
        assert updated_ride["status"] == "canceled", f"Статус не изменился на 'canceled': {updated_ride['status']}"
        
        print(f"✓ STATUS CHANGE: Статус изменён на '{updated_ride['status']}'")
        
        # Проверяем что в БД тоже изменился
        verify_resp = client.get(f"/api/v1/rides/{ride_id}")
        verify_ride = verify_resp.json()
        assert verify_ride["status"] == "canceled", "В БД статус не обновился"
        
        print(f"✓ VERIFY: Статус в БД = '{verify_ride['status']}'")


class TestDriverProfileCRUD:
    """Полная проверка CRUD для профилей водителей"""
    
    def test_driver_profile_full_cycle(self, client):
        """
        Создание профиля водителя с проверкой всех данных
        """
        # Создаём пользователя
        telegram_id = random.randint(1000000, 9999999)
        user_resp = client.post(f"/api/v1/users/{telegram_id}", json={
            "telegram_id": telegram_id,
            "first_name": "Водитель",
            "username": f"driver_{telegram_id}"
        })
        user_id = user_resp.json()["id"]
        
        print(f"\n✓ Создан пользователь для водителя: id={user_id}")
        
        # === CREATE PROFILE ===
        profile_resp = client.post("/api/v1/driver-profiles", json={
            "user_id": user_id
        })
        assert profile_resp.status_code == 201, f"Create profile failed: {profile_resp.text}"
        
        profile = profile_resp.json()
        profile_id = profile["id"]
        
        assert profile["user_id"] == user_id, "user_id не совпадает"
        
        print(f"✓ CREATE: Профиль водителя создан id={profile_id}, user_id={user_id}")
        
        # === READ ===
        get_resp = client.get(f"/api/v1/driver-profiles/{profile_id}")
        assert get_resp.status_code == 200
        
        fetched = get_resp.json()
        assert fetched["id"] == profile_id, "id не совпадает"
        assert fetched["user_id"] == user_id, "user_id не совпадает"
        
        print(f"✓ READ: Профиль получен из БД")
        
        # === DUPLICATE CHECK ===
        dup_resp = client.post("/api/v1/driver-profiles", json={"user_id": user_id})
        assert dup_resp.status_code == 409, f"Должен быть 409 Conflict, получили {dup_resp.status_code}"
        
        print(f"✓ DUPLICATE CHECK: Повторное создание корректно отклонено (409)")
        
        # === DELETE ===
        del_resp = client.delete(f"/api/v1/driver-profiles/{profile_id}")
        assert del_resp.status_code == 200
        
        # Проверяем удаление
        check_resp = client.get(f"/api/v1/driver-profiles/{profile_id}")
        assert check_resp.status_code == 404
        
        print(f"✓ DELETE: Профиль удалён и не найден (404)")


class TestTransactionsCRUD:
    """Полная проверка CRUD для транзакций"""
    
    def test_transaction_create_and_verify(self, client):
        """
        Создаём транзакцию и проверяем все поля
        """
        # Создаём пользователя
        telegram_id = random.randint(1000000, 9999999)
        user_resp = client.post(f"/api/v1/users/{telegram_id}", json={
            "telegram_id": telegram_id,
            "first_name": "Клиент транзакции",
            "username": f"txn_user_{telegram_id}"
        })
        user_id = user_resp.json()["id"]
        
        # === CREATE DEPOSIT ===
        deposit_resp = client.post("/api/v1/transactions", json={
            "user_id": user_id,
            "is_withdraw": False,
            "amount": 1000.00
        })
        assert deposit_resp.status_code == 201, f"Create deposit failed: {deposit_resp.text}"
        
        deposit = deposit_resp.json()
        
        assert deposit["user_id"] == user_id, "user_id не совпадает"
        assert deposit["is_withdraw"] == False, "is_withdraw должен быть False"
        assert deposit["amount"] == 1000.00, "amount не совпадает"
        
        print(f"\n✓ DEPOSIT: Пополнение создано id={deposit['id']}, amount={deposit['amount']}")
        
        # === CREATE WITHDRAW ===
        withdraw_resp = client.post("/api/v1/transactions", json={
            "user_id": user_id,
            "is_withdraw": True,
            "amount": 250.00
        })
        assert withdraw_resp.status_code == 201
        
        withdraw = withdraw_resp.json()
        
        assert withdraw["is_withdraw"] == True, "is_withdraw должен быть True"
        assert withdraw["amount"] == 250.00, "amount не совпадает"
        
        print(f"✓ WITHDRAW: Снятие создано id={withdraw['id']}, amount={withdraw['amount']}")
        
        # === READ ===
        get_resp = client.get(f"/api/v1/transactions/{deposit['id']}")
        assert get_resp.status_code == 200
        
        fetched = get_resp.json()
        assert fetched["amount"] == 1000.00, "amount в БД не совпадает"
        
        print(f"✓ READ: Транзакция получена из БД")
        
        # === FK VIOLATION CHECK ===
        invalid_resp = client.post("/api/v1/transactions", json={
            "user_id": 999999,
            "is_withdraw": False,
            "amount": 100.00
        })
        assert invalid_resp.status_code == 422, f"Должен быть 422 для несуществующего user_id, получили {invalid_resp.status_code}"
        
        print(f"✓ FK CHECK: Транзакция с несуществующим user_id корректно отклонена (422)")


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
        assert create_resp.status_code == 201
        
        commission = create_resp.json()
        commission_id = commission["id"]
        
        assert commission["percentage"] == 15.5, "percentage не совпадает"
        
        print(f"\n✓ CREATE: Комиссия создана id={commission_id}, percentage={commission['percentage']}%")
        
        # === READ ===
        get_resp = client.get(f"/api/v1/commissions/{commission_id}")
        assert get_resp.status_code == 200
        
        fetched = get_resp.json()
        assert fetched["percentage"] == 15.5
        
        print(f"✓ READ: Комиссия получена из БД")
        
        # === UPDATE ===
        update_resp = client.put(f"/api/v1/commissions/{commission_id}", json={
            "percentage": 20.0
        })
        assert update_resp.status_code == 200
        
        updated = update_resp.json()
        assert updated["percentage"] == 20.0, "percentage не обновился"
        
        print(f"✓ UPDATE: Комиссия обновлена percentage={updated['percentage']}%")
        
        # Проверяем в БД
        verify_resp = client.get(f"/api/v1/commissions/{commission_id}")
        assert verify_resp.json()["percentage"] == 20.0
        
        print(f"✓ VERIFY: Данные в БД обновлены")
        
        # === DELETE ===
        del_resp = client.delete(f"/api/v1/commissions/{commission_id}")
        assert del_resp.status_code == 200
        
        check_resp = client.get(f"/api/v1/commissions/{commission_id}")
        assert check_resp.status_code == 404
        
        print(f"✓ DELETE: Комиссия удалена и не найдена (404)")


class TestDataIntegrity:
    """Тесты целостности данных"""
    
    def test_count_increases_after_create(self, client):
        """
        Проверяем что счётчик увеличивается после создания
        """
        # Получаем начальное количество
        count_before = client.get("/api/v1/roles/count").json()
        
        # Создаём роль
        client.post("/api/v1/roles", json={
            "code": f"count_test_{random.randint(10000, 99999)}",
            "name": "Count Test Role"
        })
        
        # Проверяем что количество увеличилось
        count_after = client.get("/api/v1/roles/count").json()
        
        assert count_after == count_before + 1, f"Счётчик не увеличился: было {count_before}, стало {count_after}"
        
        print(f"\n✓ COUNT: Было {count_before}, стало {count_after} (+1)")
    
    def test_rides_count_type(self, client):
        """
        Проверяем что /rides/count возвращает число
        """
        resp = client.get("/api/v1/rides/count")
        assert resp.status_code == 200
        
        count = resp.json()
        assert isinstance(count, int), f"count должен быть int, получили {type(count)}"
        assert count >= 0, "count не может быть отрицательным"
        
        print(f"\n✓ RIDES COUNT: {count} (тип: int)")
