#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
set -e
cd "$(dirname "$0")/.."

COMPOSE="docker-compose"
command -v docker-compose >/dev/null 2>&1 || COMPOSE="docker compose"

echo "==> git pull"
git pull --ff-only

BOT_SERVICE="selfvpn-bot"
WEB_SERVICE="selfvpn-web"

if systemctl is-active --quiet "$BOT_SERVICE" 2>/dev/null; then
  echo "==> бот на systemd — перезапуск"
  systemctl restart "$BOT_SERVICE"
  $COMPOSE stop bot 2>/dev/null || true
else
  echo "==> бот в Docker"
  $COMPOSE up -d --build bot
fi

if systemctl is-enabled --quiet "$WEB_SERVICE" 2>/dev/null; then
  echo "==> веб на systemd — перезапуск"
  ./venv/bin/pip install -q -r requirements.txt 2>/dev/null || true
  cp deploy/selfvpn-web.service /etc/systemd/system/selfvpn-web.service
  systemctl daemon-reload
  systemctl restart "$WEB_SERVICE"
else
  echo "==> веб в Docker"
  $COMPOSE up -d --build web
fi

sleep 2
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health || echo "000")
if [ "$CODE" = "200" ]; then
  echo "OK: web HTTP $CODE"
else
  echo "WARN: web не отвечает (HTTP $CODE). Запусти: bash deploy/fix-502.sh"
fi

echo "Готово. В Telegram: /menu"
