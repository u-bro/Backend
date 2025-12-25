# Заказы / Рейсы — CRUD, State Machine, Роли, Таймауты и Аудит

Этот документ описывает, как в проекте реализованы операции с заказами (рейсами):
- CRUD (создание/чтение/обновление/удаление)
- строгая машина состояний (state machine)
- валидация переходов по ролям (client/driver/system/admin)
- таймауты и отмены с причинами
- полный аудит изменений статусов (history table)

Файлы, которые важно знать
- `app/backend/routers/ride.py` — REST‑роуты для заказов (создание, обновление, accept, finish и т.д.).
- `app/crud/ride.py` — бизнес‑логика CRUD, `change_status`, `accept` и idempotent accept.
- `app/models/ride.py` — модель `Ride` (поля: `status`, `status_reason`, `canceled_at`, `cancellation_reason`, timestamps и др.).
- `app/models/ride_status_history.py` — модель `RideStatusHistory` (аудит изменений статусов).
- `app/schemas/ride.py` — Pydantic‑схемы (`RideSchema`, `RideSchemaUpdateByClient`, `RideStatusChangeRequest` и пр.).

1) CRUD: что и где
- Создание: `POST /api/v1/rides` реализовано в `RideRouter.create` и `CrudRide.create`.
  - При создании вычисляется `expected_fare` и сохраняется snapshot тарифа.
  - Поле `status` по умолчанию устанавливается в `requested`.
- Чтение: `GET /api/v1/rides` и `GET /api/v1/rides/{id}` с правами `user/driver/admin`.
- Обновление: общий `PUT /api/v1/rides/{id}` (admin) и специальные `PUT /api/v1/rides/{id}/client` (client), `/driver` (driver).
- Удаление: `DELETE /api/v1/rides/{id}` — admin.

2) Статусы (STATUSES)
Существующие статусы (на основе кода):
- `requested`
- `driver_assigned`
- `accepted`
- `arrived`
- `started`
- `completed`
- `canceled`

3) Правила переходов — строгая машина состояний
В проекте реализована таблица/словарь разрешённых переходов `ALLOWED_TRANSITIONS`, сгруппированная по роли актёра (actor role):

- Роль `client` (заказчик):
  - `requested` -> `canceled`
  - `driver_assigned` -> `canceled`
  - `accepted` -> `canceled`

- Роль `driver`:
  - `driver_assigned` -> `accepted`  (также допускается `canceled`)
  - `accepted` -> `arrived` (или `canceled`)
  - `arrived` -> `started` (или `canceled`)
  - `started` -> `completed` (или `canceled`)

- Роль `system` (внутренние/системные переходы):
  - `requested` -> `driver_assigned` (назначение водителя системой) или `canceled`
  - `driver_assigned` -> `accepted` / `canceled`
  - `accepted` -> `arrived` / `canceled`
  - `arrived` -> `started` / `canceled`
  - `started` -> `completed` / `canceled`

Примечание: наборы переходов отображены в коде в виде словаря и применяются при вызове `change_status` (см. реализацию ниже).

4) Как реализовано изменение статуса (`change_status`) — ключевые моменты
- Вход: REST `POST /api/v1/rides/{ride_id}/status` (в роутере: `RideRouter.change_status`). Тело: `RideStatusChangeRequest` (поля: `to_status`, `actor_role`, `actor_id`, `reason`, `meta`).
- Валидация целевого статуса: сначала проверяется, что `to_status` принадлежит `STATUSES`.
- По роли определяется `role_map = ALLOWED_TRANSITIONS.get(actor_role, {})`.
- Рассчитывается `allowed_from` — список статусов, из которых роль может перейти в `to_status`.
- Если `allowed_from` пуст — бросается ошибка `status transition not allowed for this role`.
- Для атомарности и предотвращения race‑condition используется SQL с блокировкой:
  - `SELECT status FROM rides WHERE id = :ride_id FOR UPDATE` (внутри CTE `prev`) — фиксирует строку перед обновлением.
  - `UPDATE rides ... WHERE r.id = :ride_id AND (SELECT from_status FROM prev) = ANY(:allowed_from)` — обновление выполняется только если текущий статус входит в `allowed_from`.
  - Это обеспечивает безопасный, согласованный переход статуса в конкурентной среде.
- После успешного UPDATE вставляется запись в `ride_status_history` через `INSERT ... SELECT` (поля: `ride_id`, `from_status`, `to_status`, `changed_by`, `actor_role`, `reason`, `meta`, `created_at`). Вставка выполняется только когда UPDATE действительно сработал.
- Поля timestamps обновляются автоматически: `started_at`, `completed_at`, `canceled_at` проставляются в UPDATE в зависимости от `to_status`.

5) Idempotent accept / принятие рейса водителем
- В коде есть отдельный idempotent accept flow (`accept_ride_idempotent` в CRUD):
  - Конструкция `UPDATE rides SET driver_profile_id = :driver_profile_id, status = 'accepted' WHERE r.id = :ride_id AND r.status IN ('requested', 'driver_assigned') AND (r.driver_profile_id IS NULL OR r.driver_profile_id = :driver_profile_id)` — позволяет безопасно принять рейс только если он ещё не принят другой стороной.
  - При конфликте блокировки/занятости возвращается `already_taken` или `already_yours`, что позволяет клиенту корректно обработать ситуацию (idempotency / optimistic lock handling).

6) Таймауты и отмены, причины отмены
- Отмена: при переходе в `canceled` код устанавливает `canceled_at = NOW()` и `cancellation_reason` (если передан) в таблице `rides`.
- Причина отмены сохраняется в поле `cancellation_reason` модели `Ride` и также попадает в `ride_status_history.reason`.
- Таймауты: в коде есть точки, где система может переводить рейс в `canceled` или `driver_assigned` → `canceled` по таймаутам (например, если водитель не принимает назначение). Часто это реализуется фоновой задачей/cron/Celery worker. В проекте проверьте наличие задач, которые ищут старые `requested/driver_assigned` и ставят `canceled` (по меткам scheduled/created_at). Если таких задач нет, рекомендуется добавить.

7) Аудит статусов — `RideStatusHistory`
- Таблица `ride_status_history` (модель `RideStatusHistory`) содержит:
  - `id`, `ride_id`
  - `from_status`, `to_status`
  - `changed_by` (user id либо null)
  - `actor_role` (строка: `client`/`driver`/`system`/`admin`)
  - `reason` (короткая причина перехода/отмены)
  - `meta` (JSONB) — произвольные метаданные
  - `created_at` — время изменения
- При каждом успешном change_status в `ride_status_history` записывается предыдущий статус и новый, кто изменил (actor_id/actor_role), причина и meta.

8) Где проверяется роль/право на изменение
- REST‑граница: разные endpoint'ы имеют dependency‑проверки в `app/backend/deps`:
  - `require_role(['user','driver','admin'])` и узкие зависимости `require_ride_client`, `require_ride_driver` — используются в роутере `ride.py` для ограничений на create/update/accept/finish.
- Однако централизованная проверка переходов по роли выполняется в `change_status` через `actor_role` поле и `ALLOWED_TRANSITIONS`.

9) Как проверяется/тестируется (практическая инструкция)

a) Проверка разрешённых переходов (unit/integration):
 - Запустить тестовый контейнер/локальную БД и HTTP сервер (docker compose up --build -d).
 - Создать тестовый рейс (POST /api/v1/rides) с `status=requested`.
 - Выполнить POST /api/v1/rides/{ride_id}/status с телом:

```json
{ "to_status": "canceled", "actor_role": "client", "actor_id": 5, "reason": "client_cancelled" }
```

 - Ожидаемый результат: HTTP 200, `ride.status` == `canceled`, `ride.canceled_at` заполнено, в `ride_status_history` добавлена запись.

b) Попытка некорректного перехода:
 - Попробовать из роли `client` перейти `requested` -> `completed` — ожидать ошибку 4xx (ValueError / 409).

c) Race condition / concurrent accept test:
 - Параллельно отправить два запроса `accept` от двух разных driver_profile_id (или симулировать параллельные `change_status` в `driver` роли).
 - Ожидается, что один из них успешно примет, второй получит `already_taken` или `409` — проверьте код обработки в `accept_ride_idempotent`.

d) Проверка аудита:
 - SQL:
```bash
docker compose exec db psql -U postgres -d your_db -c "select id, ride_id, from_status, to_status, actor_role, changed_by, reason, created_at from ride_status_history where ride_id = <ID> order by id desc limit 20;"
```
 - Убедитесь, что для каждого change_status есть соответствующая запись.

e) Проверка отмен с причиной:
 - Выполните change_status -> `canceled` с полем `reason` и проверьте `rides.cancellation_reason` и `ride_status_history.reason`.

f) Проверка таймаутов (если есть фоновые задачи):
 - Если в проекте есть Celery/cron‑jobs для таймаутов — отключите worker и запустите задачу вручную / через тест, чтобы увидеть, что она ставит `canceled`.

10) Рекомендации по улучшению и тестированию
- Добавить явные Pydantic‑схемы и валидацию для `RideStatusChangeRequest` (если ещё не сделано) — уже есть, но проверьте поля `meta`/`reason`.
- Покрыть `change_status` unit‑тестами, включая сценарии race condition (mock DB или настоящая тестовая БД с параллельными запросами).
- Добавить мониторинг и алерты для случаев, когда `ride_status_history` не получает записей (ошибки в INSERT после UPDATE).
- Подумать о политике soft/cascade отмен и о восстановлении статусов при ошибках (rollback стратегий).

11) Быстрая сводка — SQL и проверки
- Типичный атомарный SQL, который использует код:
  - SELECT ... FOR UPDATE (получение текущего статуса)
  - UPDATE ... WHERE current_status IN allowed_from
  - INSERT INTO ride_status_history ... WHERE EXISTS (SELECT 1 FROM upd)

- Команды для проверки (примерные):
```bash
docker compose ps
docker compose logs -f app
docker compose logs -f worker
docker compose exec db psql -U postgres -d your_db -c "select * from rides where id=<ID>;"
docker compose exec db psql -U postgres -d your_db -c "select * from ride_status_history where ride_id=<ID> order by id desc limit 20;"
```

Если хотите, я выполню полный проход: найду все места в коде, где меняется `status` (включая WebSocket/Matching/Background), сгенерирую таблицу соответствий (endpoint → роль → разрешённые переходы → тесты) и добавлю её в этот документ. Скажите — надо ли добавить такую подробную таблицу и проверку всех точек, где status изменяется (router, crud, matching service, background jobs)?

*** Конец документа
