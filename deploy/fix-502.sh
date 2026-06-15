#!/bin/bash
# Восстановление сайта при 502 — только systemd, без Docker (docker-compose 1.29 ломается).
set -e
cd /opt/selfvpn

echo "============================================"
echo "  SelfVPN — fix 502 (systemd)"
echo "============================================"

git pull --ff-only 2>/dev/null || git checkout -- deploy/fix-502.sh 2>/dev/null; git pull --ff-only 2>/dev/null || true

echo ""
echo "=== 1. Python venv ==="
apt-get install -y -qq python3 python3-venv python3-pip
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q -r requirements.txt

echo ""
echo "=== 2. Проверка импорта ==="
./venv/bin/python -c "from web.app import app; print('import OK')"

echo ""
echo "=== 3. Убрать сломанный Docker-web ==="
docker-compose stop web 2>/dev/null || true
docker-compose rm -f web 2>/dev/null || true
docker compose stop web 2>/dev/null || true
docker compose rm -f web 2>/dev/null || true
docker ps -aq --filter "name=selfvpn_web" | xargs -r docker rm -f 2>/dev/null || true

echo ""
echo "=== 4. systemd selfvpn-web ==="
if [ -f deploy/selfvpn-web.service ]; then
  cp deploy/selfvpn-web.service /etc/systemd/system/selfvpn-web.service
else
  cat > /etc/systemd/system/selfvpn-web.service << 'EOF'
[Unit]
Description=SelfVPN Web Cabinet (FastAPI)
After=network.target

[Service]
WorkingDirectory=/opt/selfvpn
EnvironmentFile=/opt/selfvpn/.env
ExecStart=/opt/selfvpn/venv/bin/uvicorn web.app:app --host 127.0.0.1 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable selfvpn-web
systemctl restart selfvpn-web

echo ""
echo "=== 5. Проверка ==="
CODE="000"
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 2
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health 2>/dev/null || echo "000")
  echo "  попытка $i: HTTP $CODE"
  [ "$CODE" = "200" ] && break
done
echo "/health → HTTP $CODE"

if [ "$CODE" != "200" ]; then
  echo ""
  echo "FAIL. Логи:"
  journalctl -u selfvpn-web -n 40 --no-pager
  exit 1
fi

systemctl reload nginx 2>/dev/null || true
echo ""
echo "OK — сайт должен работать: https://daddyvpn.site"
echo "Логи: journalctl -u selfvpn-web -f"
