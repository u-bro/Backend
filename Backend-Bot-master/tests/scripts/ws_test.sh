#!/usr/bin/env bash
set -euo pipefail

# Скрипт для быстрой проверки HTTP-эндпоинтов, связанных с WebSocket
# Запускается локально при поднятом приложении (обычно http://localhost:5000)

BASE_URL=${BASE_URL:-"http://localhost:5000/api/v1"}
OUT_DIR=${OUT_DIR:-"tests/ws_results"}
mkdir -p "$OUT_DIR"

echo "Base URL: $BASE_URL"

echo "1) GET /ws/stats"
curl -s -X GET "$BASE_URL/ws/stats" -H "Accept: application/json" | jq '.' > "$OUT_DIR/ws_stats.json" || true
echo " -> saved $OUT_DIR/ws_stats.json"

echo "2) POST /ws/broadcast (no auth)"
curl -s -X POST "$BASE_URL/ws/broadcast" -H "Content-Type: application/json" -d '{"message":"broadcast test"}' | jq '.' > "$OUT_DIR/ws_broadcast.json" || true
echo " -> saved $OUT_DIR/ws_broadcast.json"

echo "3) POST /ws/notify/{user_id} (requires target connected)"
TARGET_USER_ID=${TARGET_USER_ID:-3}
curl -s -X POST "$BASE_URL/ws/notify/$TARGET_USER_ID" -H "Content-Type: application/json" -d '{"message":"notify test"}' | jq '.' > "$OUT_DIR/ws_notify_${TARGET_USER_ID}.json" || true
echo " -> saved $OUT_DIR/ws_notify_${TARGET_USER_ID}.json"

echo "4) Driver endpoints: update location/status/state"
DRIVER_USER_ID=${DRIVER_USER_ID:-3}
curl -s -X POST "$BASE_URL/ws/driver/$DRIVER_USER_ID/location" -H "Content-Type: application/json" -d '{"latitude":50.45,"longitude":30.52}' | jq '.' > "$OUT_DIR/driver_location_${DRIVER_USER_ID}.json" || true
echo " -> saved $OUT_DIR/driver_location_${DRIVER_USER_ID}.json"

curl -s -X POST "$BASE_URL/ws/driver/$DRIVER_USER_ID/status" -H "Content-Type: application/json" -d '{"status":"online"}' | jq '.' > "$OUT_DIR/driver_status_${DRIVER_USER_ID}.json" || true
echo " -> saved $OUT_DIR/driver_status_${DRIVER_USER_ID}.json"

curl -s -X GET "$BASE_URL/ws/driver/$DRIVER_USER_ID/state" -H "Accept: application/json" | jq '.' > "$OUT_DIR/driver_state_${DRIVER_USER_ID}.json" || true
echo " -> saved $OUT_DIR/driver_state_${DRIVER_USER_ID}.json"

echo "5) Drivers stats"
curl -s -X GET "$BASE_URL/ws/drivers/stats" -H "Accept: application/json" | jq '.' > "$OUT_DIR/drivers_stats.json" || true
echo " -> saved $OUT_DIR/drivers_stats.json"

echo "Готово. Просмотрите файлы в $OUT_DIR и соберите server logs для дополнительных доказательств."

echo "Примечание: некоторые эндпоинты (notify, location, status) ожидают что driver зарегистрирован в tracker или пользователь подключен по WebSocket."
