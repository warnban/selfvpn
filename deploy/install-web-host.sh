#!/bin/bash
# Веб-кабинет на хосте (systemd) — надёжнее, чем Docker-контейнер web.
set -e
cd /opt/selfvpn

echo "=== 1. Python venv ==="
apt-get install -y -qq python3 python3-venv python3-pip
if [ ! -d venv ]; then
  python3 -m venv venv
fi
./venv/bin/pip install -q -r requirements.txt

echo "=== 2. Остановить web в Docker (чтобы не конфликтовал с :8080) ==="
docker-compose stop web 2>/dev/null || true
docker-compose rm -f web 2>/dev/null || true
docker compose stop web 2>/dev/null || true
docker compose rm -f web 2>/dev/null || true

echo "=== 3. systemd web ==="
cp deploy/selfvpn-web.service /etc/systemd/system/selfvpn-web.service
systemctl daemon-reload
systemctl enable selfvpn-web
systemctl restart selfvpn-web
sleep 2
systemctl status selfvpn-web --no-pager || true

echo ""
echo "=== 4. Проверка ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/admin/login || echo "000")
echo "http://127.0.0.1:8080/admin/login → HTTP $CODE"

if [ "$CODE" != "200" ]; then
  echo ""
  echo "ОШИБКА. Логи:"
  journalctl -u selfvpn-web -n 40 --no-pager
  exit 1
fi

echo ""
echo "OK. Сайт должен открываться: https://daddyvpn.site"
echo "Логи: journalctl -u selfvpn-web -f"
