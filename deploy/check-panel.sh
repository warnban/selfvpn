#!/bin/bash
# Проверка связи selfvpn с Amnezia Panel (systemd / venv)
cd /opt/selfvpn

echo "=== .env panel settings ==="
grep -E '^PANEL_' .env 2>/dev/null | sed 's/PANEL_API_TOKEN=.*/PANEL_API_TOKEN=***hidden***/' || echo "PANEL_* не заданы"

PANEL_URL=$(grep '^PANEL_URL=' .env 2>/dev/null | cut -d= -f2-)
PANEL_URL=${PANEL_URL:-http://127.0.0.1:5000}
TOKEN=$(grep '^PANEL_API_TOKEN=' .env 2>/dev/null | cut -d= -f2-)
SERVER_ID=$(grep '^PANEL_SERVER_ID=' .env 2>/dev/null | cut -d= -f2-)
SERVER_ID=${SERVER_ID:-0}
PROTO=$(grep '^PANEL_PROTOCOL=' .env 2>/dev/null | cut -d= -f2-)
PROTO=${PROTO:-awg2}

echo ""
echo "=== amnezia-panel systemd ==="
if systemctl is-active --quiet amnezia-panel 2>/dev/null; then
  echo "active"
else
  echo "NOT RUNNING — bash deploy/install-panel-host.sh"
fi

echo ""
echo "=== Panel reachable? ($PANEL_URL) ==="
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${PANEL_URL}/docs" 2>/dev/null || echo "000")
echo "HTTP $HTTP"
if [[ "$HTTP" != "200" ]]; then
  echo "Панель недоступна. Установи: bash deploy/install-panel-host.sh"
  exit 1
fi

if [[ -z "$TOKEN" || "$TOKEN" == "awp_your_token_here" ]]; then
  echo ""
  echo ">>> PANEL_API_TOKEN не задан в .env"
  echo "    Panel → Settings → API Tokens → Create → awp_..."
  echo "    nano /opt/selfvpn/.env"
  exit 1
fi

echo ""
echo "=== Test create client API ==="
RESP=$(curl -s --max-time 30 -X POST "${PANEL_URL}/api/servers/${SERVER_ID}/connections/add" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"protocol\":\"${PROTO}\",\"name\":\"test_check\"}")
echo "$RESP" | head -c 500
echo ""

if echo "$RESP" | grep -qE 'vpn_link|client_id|clientId'; then
  echo ""
  echo "OK: Panel API работает"
else
  echo ""
  echo "FAIL: проверь PANEL_API_TOKEN и PANEL_SERVER_ID (обычно 0)"
  exit 1
fi
