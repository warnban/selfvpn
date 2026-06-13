#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
set -e
cd "$(dirname "$0")/.."

echo "==> git pull"
git pull --ff-only

BOT_SERVICE="selfvpn-bot"
USE_SYSTEMD=false
if systemctl is-active --quiet "$BOT_SERVICE" 2>/dev/null; then
  USE_SYSTEMD=true
  echo "==> бот на systemd ($BOT_SERVICE) — перезапускаем его"
  systemctl restart "$BOT_SERVICE"
  sleep 2
  systemctl status "$BOT_SERVICE" --no-pager -l | head -15
  # не даём двум ботам работать с одним токеном
  docker-compose stop bot 2>/dev/null || true
else
  echo "==> бот в Docker — пересоздаём контейнеры (down + up)"
  docker-compose down
  docker-compose up -d
  docker-compose ps
  docker exec selfvpn_bot_1 test -f /app/bot/handlers/admin.py && echo "admin.py OK" || echo "ОШИБКА: admin.py не в контейнере"
fi

echo "==> web"
docker-compose up -d web 2>/dev/null || true

echo "Готово. В Telegram: /menu"
