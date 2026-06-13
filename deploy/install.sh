#!/bin/bash
# SelfVPN — установка на Ubuntu 22.04
# Запуск: cd /opt/selfvpn && sudo bash deploy/install.sh

set -euo pipefail

APP_DIR="/opt/selfvpn"
PANEL_DIR="/opt/amnezia-panel"

echo "=== SelfVPN install ==="

if [[ $EUID -ne 0 ]]; then
  echo "Запусти от root: sudo bash deploy/install.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates ufw docker.io docker-compose-plugin python3 python3-venv python3-pip

systemctl enable --now docker

mkdir -p "$APP_DIR/data/uploads"

if [[ ! -f "$APP_DIR/.env" ]]; then
  if [[ -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "Создан $APP_DIR/.env из примера"
  fi
fi

if ! grep -q '^BOT_TOKEN=.\+' "$APP_DIR/.env" 2>/dev/null || grep -q 'BOT_TOKEN=123456789' "$APP_DIR/.env"; then
  echo ""
  echo ">>> Остановка: сначала заполни $APP_DIR/.env"
  echo "    nano $APP_DIR/.env"
  echo "    BOT_TOKEN, ADMIN_IDS, PAYMENT_CARD, ADMIN_WEB_PASSWORD, WEB_SECRET_KEY"
  exit 1
fi

cd "$APP_DIR"
docker compose up -d --build

ufw --force enable
ufw allow OpenSSH
ufw allow 8080/tcp comment 'SelfVPN web'
echo "Firewall: SSH + 8080"

# Amnezia Panel (только localhost)
if [[ ! -d "$PANEL_DIR" ]]; then
  echo "=== Установка Amnezia Panel ==="
  git clone --depth 1 https://github.com/PRVTPRO/Amnezia-Web-Panel.git "$PANEL_DIR"
  python3 -m venv "$PANEL_DIR/venv"
  "$PANEL_DIR/venv/bin/pip" install -q -r "$PANEL_DIR/requirements.txt"
fi

cat > /etc/systemd/system/amnezia-panel.service << 'EOF'
[Unit]
Description=Amnezia Web Panel
After=network.target

[Service]
WorkingDirectory=/opt/amnezia-panel
Environment=SECRET_KEY=change-me-amnezia-panel-secret
ExecStart=/opt/amnezia-panel/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now amnezia-panel

echo ""
echo "============================================"
echo "  Готово!"
echo "============================================"
echo "  Бот + кабинет:  http://72.56.124.163:8080"
echo "  Админка:         http://72.56.124.163:8080/admin/login"
echo "  Amnezia Panel:   только localhost:5000"
echo ""
echo "  Panel через SSH-туннель с твоего ПК:"
echo "  ssh -L 5000:127.0.0.1:5000 root@72.56.124.163"
echo "  затем открой http://localhost:5000"
echo ""
echo "  Логи бота:  cd $APP_DIR && docker compose logs -f bot"
echo "  Логи веб:   cd $APP_DIR && docker compose logs -f web"
echo "============================================"
