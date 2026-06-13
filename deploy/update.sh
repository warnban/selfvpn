#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
set -e
cd "$(dirname "$0")/.."

COMPOSE="docker-compose"
if ! command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker compose"
fi

echo "==> git pull"
git pull --ff-only

BOT_SERVICE="selfvpn-bot"
if systemctl is-active --quiet "$BOT_SERVICE" 2>/dev/null; then
  echo "==> бот на systemd ($BOT_SERVICE) — перезапускаем его"
  systemctl restart "$BOT_SERVICE"
  sleep 2
  systemctl status "$BOT_SERVICE" --no-pager -l | head -15
  # не даём двум ботам работать с одним токеном
  $COMPOSE stop bot 2>/dev/null || true
else
  echo "==> бот в Docker — пересоздаём контейнеры (down + up)"
  $COMPOSE down
  $COMPOSE up -d
  $COMPOSE ps
  docker exec selfvpn_bot_1 test -f /app/bot/handlers/admin.py && echo "admin.py OK" || echo "ОШИБКА: admin.py не в контейнере"
fi

echo "==> web (кабинет + скачивание .conf)"
$COMPOSE up -d --build web
sleep 3
$COMPOSE ps

WEB_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/admin/login || echo "000")
if [ "$WEB_CODE" = "200" ]; then
  echo "OK: веб отвечает HTTP $WEB_CODE"
else
  echo "ОШИБКА: веб не отвечает (HTTP $WEB_CODE). Логи:"
  docker logs $(docker ps -aq --filter "name=web" | head -1) --tail 40 2>/dev/null || true
  echo "Попробуй: bash deploy/fix-web.sh"
  exit 1
fi

echo "Готово. В Telegram: /menu"
