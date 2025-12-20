
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
