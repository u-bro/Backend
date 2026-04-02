Запуск:

Dev:
```bash
cd Backend-Bot-master/
docker compose -p ubro-dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Prod:
```bash
cd Backend-Bot-master/
docker compose -p ubro-prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```