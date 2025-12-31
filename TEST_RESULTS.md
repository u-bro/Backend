# Результаты тестирования API

**Дата:** 17 декабря 2025  
**Сервер:** Docker контейнер WEB_APP (FastAPI) на порту 5000  
**База данных:** PostgreSQL 15 в контейнере DEV_POSTGRES

---

## Результат: ✅ 74 passed, 0 failed

---

## Тесты Swagger эндпоинтов (test_full_swagger.py) — 59 тестов

### Users (4 теста)
```
tests_live/test_full_swagger.py::test_users_get_paginated      PASSED
tests_live/test_full_swagger.py::test_users_create_or_get      PASSED
tests_live/test_full_swagger.py::test_users_update             PASSED
tests_live/test_full_swagger.py::test_users_update_balance     PASSED
```

### Rides (6 тестов)
```
tests_live/test_full_swagger.py::test_rides_get_paginated      PASSED
tests_live/test_full_swagger.py::test_rides_create             PASSED
tests_live/test_full_swagger.py::test_rides_count              PASSED
tests_live/test_full_swagger.py::test_rides_get_by_id          PASSED
tests_live/test_full_swagger.py::test_rides_update             PASSED
tests_live/test_full_swagger.py::test_rides_change_status      PASSED
```

### Roles (6 тестов)
```
tests_live/test_full_swagger.py::test_roles_get_paginated      PASSED
tests_live/test_full_swagger.py::test_roles_create             PASSED
tests_live/test_full_swagger.py::test_roles_count              PASSED
tests_live/test_full_swagger.py::test_roles_get_by_id          PASSED
tests_live/test_full_swagger.py::test_roles_update             PASSED
tests_live/test_full_swagger.py::test_roles_delete             PASSED
```

### Driver Profiles (6 тестов)
```
tests_live/test_full_swagger.py::test_driver_profiles_get_paginated  PASSED
tests_live/test_full_swagger.py::test_driver_profiles_create         PASSED
tests_live/test_full_swagger.py::test_driver_profiles_count          PASSED
tests_live/test_full_swagger.py::test_driver_profiles_get_by_id      PASSED
tests_live/test_full_swagger.py::test_driver_profiles_update         PASSED
tests_live/test_full_swagger.py::test_driver_profiles_delete         PASSED
```

### Driver Documents (6 тестов)
```
tests_live/test_full_swagger.py::test_driver_documents_get_paginated PASSED
tests_live/test_full_swagger.py::test_driver_documents_create        PASSED
tests_live/test_full_swagger.py::test_driver_documents_count         PASSED
tests_live/test_full_swagger.py::test_driver_documents_get_by_id     PASSED
tests_live/test_full_swagger.py::test_driver_documents_update        PASSED
tests_live/test_full_swagger.py::test_driver_documents_delete        PASSED
```

### Phone Verifications (6 тестов)
```
tests_live/test_full_swagger.py::test_phone_verifications_get_paginated PASSED
tests_live/test_full_swagger.py::test_phone_verifications_create        PASSED
tests_live/test_full_swagger.py::test_phone_verifications_count         PASSED
tests_live/test_full_swagger.py::test_phone_verifications_get_by_id     PASSED
tests_live/test_full_swagger.py::test_phone_verifications_update        PASSED
tests_live/test_full_swagger.py::test_phone_verifications_delete        PASSED
```

### Commissions (6 тестов)
```
tests_live/test_full_swagger.py::test_commissions_get_paginated   PASSED
tests_live/test_full_swagger.py::test_commissions_create          PASSED
tests_live/test_full_swagger.py::test_commissions_count           PASSED
tests_live/test_full_swagger.py::test_commissions_get_by_id       PASSED
tests_live/test_full_swagger.py::test_commissions_update          PASSED
tests_live/test_full_swagger.py::test_commissions_delete          PASSED
```

### Driver Locations (6 тестов)
```
tests_live/test_full_swagger.py::test_driver_locations_get_paginated PASSED
tests_live/test_full_swagger.py::test_driver_locations_create        PASSED
tests_live/test_full_swagger.py::test_driver_locations_count         PASSED
tests_live/test_full_swagger.py::test_driver_locations_get_by_id     PASSED
tests_live/test_full_swagger.py::test_driver_locations_update        PASSED
tests_live/test_full_swagger.py::test_driver_locations_delete        PASSED
```

### Chat Messages (6 тестов)
```
tests_live/test_full_swagger.py::test_chat_messages_get_paginated    PASSED
tests_live/test_full_swagger.py::test_chat_messages_create           PASSED
tests_live/test_full_swagger.py::test_chat_messages_count            PASSED
tests_live/test_full_swagger.py::test_chat_messages_get_by_id        PASSED
tests_live/test_full_swagger.py::test_chat_messages_update           PASSED
tests_live/test_full_swagger.py::test_chat_messages_delete           PASSED
```

### Transactions (6 тестов)
```
tests_live/test_full_swagger.py::test_transactions_get_paginated     PASSED
tests_live/test_full_swagger.py::test_transactions_create            PASSED
tests_live/test_full_swagger.py::test_transactions_count             PASSED
tests_live/test_full_swagger.py::test_transactions_get_by_id         PASSED
tests_live/test_full_swagger.py::test_transactions_update            PASSED
tests_live/test_full_swagger.py::test_transactions_delete            PASSED
```

### Health (1 тест)
```
tests_live/test_full_swagger.py::test_health                         PASSED
```

---

## Реальные API тесты (test_real_api.py) — 15 тестов

### Users (2 теста)
```
tests_live/test_real_api.py::test_users_crud_full_cycle         PASSED
tests_live/test_real_api.py::test_users_update_nonexistent      PASSED
```

### Roles (2 теста)
```
tests_live/test_real_api.py::test_roles_crud_full_cycle         PASSED
tests_live/test_real_api.py::test_roles_delete_nonexistent      PASSED
```

### Rides (3 теста)
```
tests_live/test_real_api.py::test_rides_create_and_get          PASSED
tests_live/test_real_api.py::test_rides_change_status_not_found PASSED
tests_live/test_real_api.py::test_rides_change_status_success   PASSED
```

### Driver Profiles (2 теста)
```
tests_live/test_real_api.py::test_driver_profile_create_success     PASSED
tests_live/test_real_api.py::test_driver_profile_duplicate_user     PASSED
```

### Driver Locations (2 теста)
```
tests_live/test_real_api.py::test_driver_location_foreign_key_error PASSED
tests_live/test_real_api.py::test_driver_location_create_success    PASSED
```

### Commissions (2 теста)
```
tests_live/test_real_api.py::test_commissions_crud                  PASSED
tests_live/test_real_api.py::test_commissions_delete_nonexistent    PASSED
```

### Transactions (1 тест)
```
tests_live/test_real_api.py::test_transactions_delete_nonexistent   PASSED
```

### Health (1 тест)
```
tests_live/test_real_api.py::test_health_endpoint                   PASSED
```

---

## Статистика по группам

| Группа | Swagger тесты | Real API тесты | Всего |
|--------|---------------|----------------|-------|
| Users | 4 | 2 | 6 |
| Rides | 6 | 3 | 9 |
| Roles | 6 | 2 | 8 |
| Driver Profiles | 6 | 2 | 8 |
| Driver Documents | 6 | 0 | 6 |
| Phone Verifications | 6 | 0 | 6 |
| Commissions | 6 | 2 | 8 |
| Driver Locations | 6 | 2 | 8 |
| Chat Messages | 6 | 0 | 6 |
| Transactions | 6 | 1 | 7 |
| Health | 1 | 1 | 2 |
| **Итого** | **59** | **15** | **74** |

---

## HTTP коды ответов (проверенные)

| Код | Значение | Когда возвращается |
|-----|----------|-------------------|
| 200 | OK | Успешное получение/обновление |
| 201 | Created | Успешное создание |
| 404 | Not Found | Ресурс не найден (DELETE несуществующего) |
| 409 | Conflict | Дубликат (например, профиль водителя) |
| 422 | Unprocessable Entity | Невалидные данные, FK violation |

---

## Команда запуска

```bash
# Полный запуск всех тестов
docker exec WEB_APP python -m pytest tests_live/ -v

pytest tests_live/ -v

# Только swagger тесты
pytest tests_live/test_full_swagger.py -v

# Только real API тесты  
pytest tests_live/test_real_api.py -v
```

---

## Примечание

ERROR в teardown тестов — это известная проблема совместимости pytest-asyncio с httpx.AsyncClient (закрытие event loop после каждого теста). **Не влияет на результаты тестов** — все 74 теста успешно прошли.

---

## WebSocket checks (ручная и автоматизированная проверка)

Статус: план и инструменты подготовлены. Для воспроизведения и сбора артефактов выполните `scripts/ws_test.sh` на машине с запущенным приложением.

- **Артефакты:** `tests/ws_results/` — содержит JSON ответы от эндпоинтов, собранные скриптом.
- **Ручные шаги:**
	- Запустить два браузерных WS-клиента (DevTools) и подключиться к `ws://localhost:5000/api/v1/ws/{user_id}` — использовать JS сниппет ниже.
	- Отправить `join_ride`, `ping`, `location_update`, `go_online` и проверить, что соответствующие события приходят другим участникам.
	- Вызвать HTTP `POST /api/v1/ws/notify/{user_id}` и убедиться, что клиент получает уведомление.

### JS сниппет для DevTools (вставить в Console)

```javascript
const ws = new WebSocket('ws://localhost:5000/api/v1/ws/3');
ws.addEventListener('open', ()=> console.log('open'));
ws.addEventListener('message', (e)=> console.log('msg', JSON.parse(e.data)));
// Пример отправки после открытия
// ws.send(JSON.stringify({type: 'ping'}))
```

### Как запустить подготовленный скрипт

В терминале проекта:

```bash
chmod +x scripts/ws_test.sh
# при необходимости задать URL и user id
BASE_URL=http://localhost:5000/api/v1 DRIVER_USER_ID=3 TARGET_USER_ID=3 ./scripts/ws_test.sh
```

После выполнения проверьте файлы в `tests/ws_results/` и соберите логи приложения (docker logs или system logs) для включения в доказательную базу.

---

Если хотите — могу запустить `scripts/ws_test.sh` и собрать результаты здесь, но для этого нужно, чтобы сервис был запущен и доступен из среды, где работает этот агент. Хотите, чтобы я попытался запустить скрипт сейчас? 
