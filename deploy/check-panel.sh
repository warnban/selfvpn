#!/bin/bash
# Проверка связи бота с Amnezia Panel
set -e
cd /opt/selfvpn

echo "=== .env panel settings ==="
grep -E '^PANEL_' .env | sed 's/PANEL_API_TOKEN=.*/PANEL_API_TOKEN=***hidden***/'

PANEL_URL=$(grep '^PANEL_URL=' .env | cut -d= -f2-)
TOKEN=$(grep '^PANEL_API_TOKEN=' .env | cut -d= -f2-)
SERVER_ID=$(grep '^PANEL_SERVER_ID=' .env | cut -d= -f2-)
PROTO=$(grep '^PANEL_PROTOCOL=' .env | cut -d= -f2-)

echo ""
echo "=== Panel reachable from host? ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "${PANEL_URL}/docs" || echo "FAIL"

echo ""
echo "=== Panel reachable from bot container? ==="
docker-compose exec -T bot python -c "
import httpx, os
url = os.environ.get('PANEL_URL','').rstrip('/')
try:
    r = httpx.get(url + '/docs', timeout=5)
    print('HTTP', r.status_code)
except Exception as e:
    print('ERROR:', e)
"

if [[ -z "$TOKEN" || "$TOKEN" == "awp_your_token_here" ]]; then
  echo ""
  echo ">>> PANEL_API_TOKEN не задан! См. инструкцию ниже."
  exit 1
fi

echo ""
echo "=== Test create client API ==="
curl -s -X POST "${PANEL_URL}/api/servers/${SERVER_ID}/connections/add" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"protocol\":\"${PROTO}\",\"name\":\"test_check\"}" | head -c 500
echo ""

echo ""
echo "=== Amnezia panel systemd ==="
systemctl is-active amnezia-panel 2>/dev/null || echo "amnezia-panel service NOT installed"
