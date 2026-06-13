#!/bin/bash
# Восстановление сайта при 502 Bad Gateway.
set -e
cd /opt/selfvpn

echo "============================================"
echo "  SelfVPN — fix 502"
echo "============================================"

git pull --ff-only 2>/dev/null || true

echo ""
echo "=== Порт 8080 ==="
if command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep ':8080' || echo "никто не слушает 8080"
fi

echo ""
echo "=== Пробуем веб через systemd (рекомендуется) ==="
chmod +x deploy/install-web-host.sh
bash deploy/install-web-host.sh

echo ""
echo "=== Nginx ==="
systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null || true

PUBLIC=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: daddyvpn.site" http://127.0.0.1/admin/login 2>/dev/null || echo "000")
echo "Через nginx (daddyvpn.site): HTTP $PUBLIC"

if [ "$PUBLIC" = "200" ]; then
  echo ""
  echo "Готово — 502 должна уйти. Обнови страницу в браузере."
else
  echo ""
  echo "Локально web OK, но nginx всё ещё $PUBLIC."
  echo "Проверь конфиг:"
  echo "  grep -R proxy_pass /etc/nginx/sites-enabled/"
  echo "Должно быть: proxy_pass http://127.0.0.1:8080;"
fi
