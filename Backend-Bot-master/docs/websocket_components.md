# Обзор компонентов WebSocket (Backend-Bot)

Файл содержит карту расположения ключевых классов/функций и объяснения, кто за что отвечает, как реализована валидация/авторизация, очередь сохранения сообщений и ограничения.

**Файлы и главные сущности**

- [app/backend/routers/websocket.py](app/backend/routers/websocket.py)
  - Класс: `DriverWebsocketRouter (BaseWebsocketRouter)`
    - `setup_routes()` — регистрирует WebSocket-роут `/api/v1/ws/{user_id}` и REST endpoints для управления WS (stats, notify, broadcast, driver location/status/state, drivers stats).
    - `websocket_endpoint(websocket, user_id, token)` — входная точка для WS: вызывает `self.run(...)` (реализация в `BaseWebsocketRouter`).
    - lifecycle handlers:
      - `on_connect` — вызывается при установлении сессии; вызывает `manager.connect(websocket, user_id)` и отправляет сообщение `type: connected` клиенту.
      - `on_disconnect` — вызывает `manager.disconnect(...)`.
      - `on_error` — логирование ошибок.
    - зарегистрированные message handlers (через `register_handler`):
      - `handle_ping` — отвечает `{type: "pong"}`.
      - `handle_join_ride` — проверяет `payload.ride_id`, вызывает `chat_service.can_access_ride_chat(...)`, при успехе вызывает `manager.join_ride` и возвращает `joined_ride`.
      - `handle_leave_ride` — вызывает `manager.leave_ride`.
      - `handle_chat_message` — основной путь отправки сообщения (модерация, rate-limit, enqueue для persistence, broadcast через manager).
      - `handle_location_update`, `handle_go_online`, `handle_go_offline`, `handle_pause` — драйверные события (driver_tracker + рассылка в ride).
    - REST методы в том же роутере: `get_websocket_stats`, `send_notification`, `broadcast_message`, `update_driver_location`, `update_driver_status`, `get_driver_state`, `get_drivers_stats`.

- [app/services/websocket_manager.py](app/services/websocket_manager.py)
  - Класс: `ConnectionManager`
    - Хранит `active_connections: Dict[user_id, List[WebSocket]]` и `ride_participants: Dict[ride_id, set(user_id)]`.
    - `connect(websocket, user_id)` — `await websocket.accept()`; добавляет соединение в `active_connections`.
    - `disconnect(websocket, user_id)` — удаляет соединение.
    - `is_connected(user_id)`, `get_online_users()`, `get_connection_count()` — вспомогательные.
    - `send_personal_message(user_id, message)` — посылает JSON всем ws соединениям пользователя, добавляет `timestamp`, чистит упавшие соединения.
    - `broadcast(message, exclude_user_id=None)` — шлёт сообщение всем подключённым пользователям (с timestamp).
    - `join_ride(ride_id, user_id)`, `leave_ride(ride_id, user_id)` — управление группой участников рейса.
    - `send_to_ride(ride_id, message, exclude_user_id=None)` — шлёт всем участникам ride (через `send_personal_message`).
  - Экземпляр: `manager = ConnectionManager()` используется в роутере.

- [app/services/chat_service.py](app/services/chat_service.py)
  - Класс: `ChatService` (экземпляр `chat_service`)
    - Moderation:
      - `_normalize_text`, `_contains_banned_words`, `_censor_text` — проверка и цензура (используется библиотека `better-profanity` + собственный словарь `BANNED_WORDS`).
      - `moderate_message(text) -> ModerationResult` — проверка длины, пустоты, profanity; возвращает `filtered` текст и флаг `passed`.
    - Rate limiting:
      - В памяти хранится `_message_timestamps[user_id]`, параметры `rate_limit_messages` и `rate_limit_period`.
      - `check_rate_limit(user_id)` — проверяет и регистрирует сообщение для реализации простого rate-limit.
    - Persistence API (DB):
      - `save_message(session, ride_id, sender_id, text, ...)` — сохраняет `ChatMessage` в базе с поддержкой дедупликации по `idempotency_key` (при наличии ключа сначала ищет существующее сообщение и возвращает его, если найдено). Выполняет `session.add`, `await session.flush()` и `await session.refresh(message)` и возвращает Pydantic-структуру `ChatMessageSchema`.
      - `get_chat_history(session, ride_id, ...)`, `soft_delete_message`, `edit_message` — стандартные CRUD для сообщений (soft delete, edit с модерацией).
    - Authorization helper:
      - `can_access_ride_chat(session, user_id, ride_id)` — проверяет доступ: возвращает True если user является `ride.client_id`, или `ride.driver_profile.user_id`, или роль `admin`.
    - Stats / тестовые методы: `get_stats`, `test_profanity_detection`.

- [app/tasks/chat_tasks.py](app/tasks/chat_tasks.py)
  - Celery task `save_chat_message` (обёртка `celery_app.task`) — принимает `payload` из WS handler, внутри запускает `asyncio.run(_save_message_async(payload))`.
  - `_save_message_async(payload)` — использует `async_session_maker()` чтобы получить `AsyncSession`, вызывает `chat_service.save_message(...)` и возвращает результат.
  - retry policy: `bind=True, max_retries=5, default_retry_delay=10` + на ошибки делает `self.retry(...)`.

- `app/backend/routers/websocket_base.py`
  - `BaseWebsocketRouter` — базовая логика `run`:
    - `run(websocket, **context)` вызывает `await on_connect(...)`, затем читает `receive_json` в loop и вызывает `dispatch_message(...)`.
    - `dispatch_message` — берёт `message_type = data.get('type')`, находит handler в `_handlers` и вызывает его.


---

# Поток сохранения сообщения (детально)

1. Клиент отправляет JSON через WebSocket с `type: "chat_message"` и `payload`.
2. В `DriverWebsocketRouter.handle_chat_message`:
   - Берётся `user_id` из context (установлен на handshake), извлекаются `ride_id` и `text` из `data` (payload может быть вложенным — роутер ожидает `data.get('ride_id')`).
   - Вызывается `chat_service.moderate_message(text)` — если модерация не пройдена, отправляется ошибка клиенту и flow останавливается.
   - Вызывается `chat_service.check_rate_limit(user_id)` — если превышение — отправляется ошибка.
   - Генерируется `idempotency_key = uuid.uuid4().hex` (если клиент не передал собственный ключ).
   - Формируется `payload` для фоновой сохранения (с `idempotency_key`, `ride_id`, `sender_id`, `text`, ...).
   - Вызов `save_chat_message.delay(payload)` — задача ставится в очередь Celery.
   - Немедленное real-time вещание: `await manager.send_to_ride(ride_id, message)` — чтобы участники увидели сообщение почти мгновенно.
3. Celery worker берет задачу `save_chat_message` и выполняет `_save_message_async(payload)`:
   - Создаётся `AsyncSession` через `async_session_maker()`.
   - Вызывается `await chat_service.save_message(session, ...)`.
   - `save_message` делает dedup по `idempotency_key`: если запись с таким ключом уже есть — возвращает её; иначе создаёт `ChatMessage`, добавляет в сессию и flush/refresh.
   - По успешному сохранению задача возвращает данные (и при ошибках делает retry).

Это обеспечивает: быстрый UX (broadcast сразу) + надежность сохранения (фоновая задача + дедупликация).

---

# Авторизация и доступы

- Handshake / получение контекста `user_id` и `token` передаётся при подключении (`/api/v1/ws/{user_id}?token=...`).
  - В коде роутера `websocket_endpoint(..., user_id, token)` передаётся в `run`. (Реальная валидация токена — в проекте обычно реализуется либо в момент `websocket_endpoint` до `run`, либо в `on_connect`; в текущем коде проверка принадлежности к чату происходит в `can_access_ride_chat`.)
- Правила доступа к чату (`can_access_ride_chat`):
  - Если у пользователя роль `admin` (role.code == 'admin') — доступ разрешён.
  - Если `user_id == ride.client_id` — доступ разрешён.
  - Если `ride.driver_profile.user_id == user_id` — доступ разрешён.
  - Иначе — доступ запрещён (ws отправляет `{type: "error", message: "Access denied to ride chat"}`).

Dependency: `require_ride_chat_access`
- Файл: [app/backend/deps/require_ride_chat_access.py](app/backend/deps/require_ride_chat_access.py)
- Описание: FastAPI-зависимость, которая проверяет доступ к чату рейса. Разрешает доступ только если текущий пользователь — `admin`, клиент рейса или водитель, привязанный к `ride.driver_profile.user_id`. Возвращает объект `Ride` при успехе или вызывает `HTTPException(403)`.
- Пример использования в REST-роуте:

  - Вариант с параметром `ride_id`:

    - `async def get_chat_history(ride: Ride = Depends(require_ride_chat_access)):` — в хендлере будет доступен `ride` и, если зависимость вернула, значит доступ разрешён.

  - Для WebSocket-хендлеров: сначала извлечь `user` из токена/контекста, затем вызвать `chat_service.can_access_ride_chat(session, user.id, ride_id)` или использовать аналогичную логику на этапе `join_ride`.

Эта зависимость обеспечивает централизованную проверку прав доступа к чатам и её удобно применять в REST-эндпоинтах и в коде для унификации логики авторизации.

- Проверка ролей на REST endpoints выполняется через зависимости `require_role` и другие в `app/backend/deps/*`.

---

# Ограничения и модерация

- Rate-limit реализован в `ChatService.check_rate_limit` (в памяти, простая реализация):
  - `rate_limit_messages` сообщений за `rate_limit_period` секунд (по умолчанию 10/60s).
  - Подходит для базовой защиты; для продакшна рекомендуется использовать Redis-based sliding window / token bucket.

- Модерация:
  - Используется `better-profanity` + собственный список `BANNED_WORDS` и нормализация (leet subs).
  - `moderate_message` возвращает `ModerationResult` с `filtered` текстом и причиной.

---

# Где что находится (список ключевых символов)

- `app/backend/routers/websocket.py` — роуты WS и REST, handlers (`handle_chat_message`, `handle_join_ride`, ...).
- `app/services/websocket_manager.py` — `ConnectionManager` / `manager` — отвечает за хранение соединений, рассылки, группы ride.
- `app/services/chat_service.py` — `ChatService` / `chat_service` — модерация, rate-limit, сохранение/получение сообщений (DB), проверка доступа.
- `app/tasks/chat_tasks.py` — Celery task `save_chat_message` и helper `_save_message_async`.
- `app/backend/routers/websocket_base.py` — `BaseWebsocketRouter` — общий loop приёма сообщений и dispatch.
- `app/backend/deps/` — зависимости для авторизации и проверок (require_role, require_ride_client и т.д.).

---

# Рекомендации и возможные улучшения (быть готовыми отметить в доке)

- Перенести rate-limit в Redis (либо использовать внешнюю реализацию) для корректной работы на нескольких инстансах.
- Явно валидировать и логировать `payload` входящих сообщений (schema для каждого типа). Сейчас обработчики читают поля напрямую.
- Сделать отдельный слой авторизации/валидации на handshake и централизовать проверку token -> user mapping.
- Добавить event audit/log для модерации/отклонённых сообщений.

---

Если нужно, я могу:
- расширить файл примерами JSON для каждого message type (примеры `payload`);
- добавить sequence diagram (текстово) для потока "клиент → ws handler → Celery → DB";
- сгенерировать упрощённую ER‑схему таблицы `chat_messages` (если нужно).

Файл сохранён как: `docs/websocket_components.md`.
