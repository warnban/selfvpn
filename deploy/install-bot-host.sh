#!/bin/bash
# Бот на хосте (systemd), веб в Docker — обходит проблему Docker → Panel
set -e
cd /opt/selfvpn

echo "=== 1. Python venv ==="
apt-get install -y -qq python3 python3-venv python3-pip
python3 -m venv venv
./venv/bin/pip install -q -r requirements.txt

echo "=== 2. .env: PANEL_URL для бота на хосте ==="
if grep -q '^PANEL_URL=' .env; then
  sed -i 's|^PANEL_URL=.*|PANEL_URL=http://127.0.0.1:5000|' .env
else
  echo 'PANEL_URL=http://127.0.0.1:5000' >> .env
fi
grep '^PANEL_URL=' .env

echo "=== 3. Остановить bot-контейнер (если был) ==="
docker-compose stop bot 2>/dev/null || true
docker-compose rm -f bot 2>/dev/null || true

echo "=== 4. Только web в Docker ==="
docker-compose up -d --build

echo "=== 5. systemd бот ==="
cp deploy/selfvpn-bot.service /etc/systemd/system/selfvpn-bot.service
systemctl daemon-reload
systemctl enable --now selfvpn-bot

sleep 2
systemctl status selfvpn-bot --no-pager

echo ""
echo "=== 6. Тест Panel с хоста ==="
curl -s -o /dev/null -w "Panel HTTP %{http_code}\n" http://127.0.0.1:5000/docs

echo ""
echo "Готово. Проверь VPN в Telegram: 🔐 Подключить VPN"
echo "Логи бота: journalctl -u selfvpn-bot -f"
