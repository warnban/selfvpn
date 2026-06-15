#!/bin/bash
# Проверка, что фикс resend задеплоен и отвечает быстро
set -e
cd /opt/selfvpn

echo "=== Git ==="
git log -1 --oneline
if ! grep -q "background_tasks" web/auth_routes.py; then
  echo "ОШИБКА: старый код — выполни git pull"
  exit 1
fi
echo "OK: background_tasks найден"

echo ""
echo "=== Health ==="
curl -sf --max-time 5 http://127.0.0.1:8080/health && echo " OK" || { echo "FAIL"; exit 1; }

echo ""
echo "=== Resend (без токена, должен редиректнуть за <2с) ==="
START=$(date +%s%N)
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  -X POST http://127.0.0.1:8080/auth/resend-verification \
  -d "next_url=/cabinet" \
  -H "Content-Type: application/x-www-form-urlencoded")
END=$(date +%s%N)
MS=$(( (END - START) / 1000000 ))
echo "HTTP $HTTP за ${MS}ms (ожидается 303 за <2000ms)"
if [ "$HTTP" != "303" ] && [ "$HTTP" != "307" ]; then
  echo "Неожиданный код — смотри journalctl -u selfvpn-web"
  exit 1
fi
if [ "$MS" -gt 2000 ]; then
  echo "СЛИШКОМ МЕДЛЕННО — SMTP всё ещё блокирует запрос"
  exit 1
fi

TOKEN=$(sqlite3 data/bot.db "SELECT cabinet_token FROM users WHERE email IS NOT NULL AND email_verified=0 LIMIT 1;" 2>/dev/null || true)
if [ -n "$TOKEN" ]; then
  echo ""
  echo "=== Resend с cabinet_token ==="
  START=$(date +%s%N)
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    -X POST "http://127.0.0.1:8080/auth/resend-verification" \
    -d "cabinet_token=${TOKEN}&next_url=/cabinet" \
    -H "Content-Type: application/x-www-form-urlencoded")
  END=$(date +%s%N)
  MS=$(( (END - START) / 1000000 ))
  echo "HTTP $HTTP за ${MS}ms"
fi

echo ""
echo "Готово. В браузере обнови кабинет с Ctrl+Shift+R (без кэша)."
