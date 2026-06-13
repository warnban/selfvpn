#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
set -e
cd "$(dirname "$0")/.."

echo "==> git pull"
git pull --ff-only

echo "==> пересоздаём контейнеры (down + up — обход бага docker-compose 1.29)"
docker-compose down
docker-compose up -d

echo "==> status"
docker-compose ps

echo "==> проверка: код монтируется с диска?"
docker exec selfvpn_bot_1 test -f /app/bot/handlers/admin.py && echo "admin.py OK" || echo "ОШИБКА: admin.py не найден в контейнере"
docker exec selfvpn_bot_1 grep -q "ADM PANEL" /app/bot/keyboards/main.py && echo "admin buttons OK" || echo "ОШИБКА: старый main.py"

echo "Готово."
