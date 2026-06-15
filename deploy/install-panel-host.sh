#!/bin/bash
# Amnezia Panel на том же VPS (systemd, только localhost:5000)
set -euo pipefail

PANEL_DIR="/opt/amnezia-panel"

if [[ $EUID -ne 0 ]]; then
  echo "Запусти от root: sudo bash deploy/install-panel-host.sh"
  exit 1
fi

echo "=== Amnezia Panel ==="

apt-get install -y -qq git python3 python3-venv python3-pip curl

if [[ ! -d "$PANEL_DIR" ]]; then
  echo "Клонирую в $PANEL_DIR ..."
  git clone --depth 1 https://github.com/PRVTPRO/Amnezia-Web-Panel.git "$PANEL_DIR"
fi

if [[ ! -x "$PANEL_DIR/venv/bin/python" ]]; then
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
systemctl enable amnezia-panel
systemctl restart amnezia-panel

sleep 2
if ! systemctl is-active --quiet amnezia-panel; then
  echo "FAIL: amnezia-panel не запустилась"
  journalctl -u amnezia-panel -n 30 --no-pager
  exit 1
fi

HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:5000/docs || echo "000")
echo "Panel HTTP $HTTP (ожидается 200)"

if [[ "$HTTP" != "200" ]]; then
  journalctl -u amnezia-panel -n 20 --no-pager
  exit 1
fi

echo ""
echo "Панель запущена на http://127.0.0.1:5000"
echo ""
echo "Дальше:"
echo "  1. SSH-туннель с ПК: ssh -L 5000:127.0.0.1:5000 root@$(hostname -I | awk '{print $1}')"
echo "  2. Открой http://localhost:5000 → admin / admin (смени пароль)"
echo "  3. Servers → Add Server → IP NL VPN, SSH root"
echo "  4. Settings → API Tokens → Create → вставь в /opt/selfvpn/.env как PANEL_API_TOKEN"
echo "  5. systemctl restart selfvpn-web selfvpn-bot"
echo ""
echo "Если панель была на старом сервере — быстрее скопировать:"
echo "  rsync -avz root@72.56.124.163:/opt/amnezia-panel/ /opt/amnezia-panel/"
echo "  systemctl restart amnezia-panel"
