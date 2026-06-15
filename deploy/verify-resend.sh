#!/bin/bash
# Проверка, что фикс resend задеплоен и отвечает быстро
cd /opt/selfvpn

fail() {
  echo "FAIL: $1"
  echo ""
  echo "=== systemctl status ==="
  systemctl status selfvpn-web --no-pager -l 2>/dev/null | tail -20 || true
  echo ""
  echo "=== journalctl (последние 30 строк) ==="
  journalctl -u selfvpn-web -n 30 --no-pager 2>/dev/null || true
  exit 1
}

echo "=== Git ==="
git log -1 --oneline
if ! grep -q "background_tasks" web/auth_routes.py; then
  fail "старый код — выполни git pull"
fi
echo "OK: background_tasks найден"

echo ""
echo "=== Service ==="
if ! systemctl is-active --quiet selfvpn-web; then
  fail "selfvpn-web не запущен — systemctl restart selfvpn-web"
fi
echo "OK: selfvpn-web active"

echo ""
echo "=== Health ==="
for i in 1 2 3 4 5; do
  if curl -sf --max-time 3 http://127.0.0.1:8080/health >/dev/null; then
    echo "OK"
    break
  fi
  if [ "$i" -eq 5 ]; then
    fail "http://127.0.0.1:8080/health не отвечает"
  fi
  sleep 1
done

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
  fail "неожиданный HTTP $HTTP"
fi
if [ "$MS" -gt 2000 ]; then
  fail "ответ слишком медленный (${MS}ms)"
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
