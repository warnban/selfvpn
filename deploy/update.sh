#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
set -e
cd "$(dirname "$0")/.."

git pull --ff-only 2>/dev/null || { git checkout -- deploy/fix-502.sh 2>/dev/null; git pull --ff-only; }

if [ -f deploy/build-landing.sh ] && command -v npm >/dev/null 2>&1; then
  echo "==> сборка лендинга"
  bash deploy/build-landing.sh
fi

BOT_SERVICE="selfvpn-bot"
WEB_SERVICE="selfvpn-web"

if systemctl is-active --quiet "$BOT_SERVICE" 2>/dev/null; then
  echo "==> бот systemd — restart"
  systemctl restart "$BOT_SERVICE"
  docker-compose stop bot 2>/dev/null || true
else
  echo "==> бот Docker (если нужен — см. deploy/install-bot-host.sh)"
  docker-compose stop bot 2>/dev/null || true
fi

echo "==> веб systemd"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q -r requirements.txt
if [ -f deploy/selfvpn-web.service ]; then
  cp deploy/selfvpn-web.service /etc/systemd/system/selfvpn-web.service
fi
systemctl daemon-reload
systemctl enable selfvpn-web 2>/dev/null || bash deploy/fix-502.sh
systemctl restart selfvpn-web

sleep 2
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health || echo "000")
echo "web /health → HTTP $CODE"
[ "$CODE" = "200" ] || bash deploy/fix-502.sh

echo "Готово."
