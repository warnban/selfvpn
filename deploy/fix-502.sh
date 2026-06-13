#!/bin/bash
# Восстановление сайта при 502 Bad Gateway (nginx жив, uvicorn на :8080 — нет).
set -e
cd /opt/selfvpn

COMPOSE="docker-compose"
if ! command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker compose"
fi

echo "============================================"
echo "  SelfVPN — fix 502"
echo "============================================"

echo ""
echo "=== 1. Git ==="
git log -1 --oneline 2>/dev/null || true

echo ""
echo "=== 2. Кто слушает порт 8080 ==="
if ss -tlnp 2>/dev/null | grep -q ':8080'; then
  ss -tlnp | grep ':8080' || true
else
  echo "НИКТО не слушает 8080 — nginx отдаёт 502"
fi

echo ""
echo "=== 3. Docker ==="
$COMPOSE ps -a 2>/dev/null || docker ps -a | grep selfvpn || true

echo ""
echo "=== 4. Проверка импорта web в контейнере ==="
$COMPOSE run --rm --no-deps web python -c "from web.app import app; print('import OK')" 2>&1 || echo "ОШИБКА импорта — см. traceback выше"

echo ""
echo "=== 5. Пересборка и запуск web ==="
$COMPOSE up -d --build --force-recreate web
sleep 5
$COMPOSE ps

echo ""
echo "=== 6. Логи web (последние 40 строк) ==="
$COMPOSE logs web --tail 40 2>/dev/null || docker logs $(docker ps -aq --filter "name=web" | head -1) --tail 40

echo ""
echo "=== 7. Проверка localhost ==="
LOCAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/admin/login || echo "000")
echo "http://127.0.0.1:8080/admin/login → HTTP $LOCAL_CODE"

if [ "$LOCAL_CODE" = "200" ]; then
  echo ""
  echo "OK: веб работает локально."
  echo "Если снаружи всё ещё 502 — перезагрузи nginx:"
  echo "  systemctl reload nginx"
  PUBLIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: daddyvpn.site" http://127.0.0.1/admin/login 2>/dev/null || echo "000")
  echo "Через nginx: HTTP $PUBLIC_CODE"
else
  echo ""
  echo "FAIL: веб не поднялся. Частые причины:"
  echo "  • нет .env или пустой BOT_TOKEN"
  echo "  • ошибка в коде (traceback в логах выше)"
  echo "  • порт 8080 занят другим процессом"
  echo ""
  echo "Попробуй вручную:"
  echo "  cd /opt/selfvpn"
  echo "  $COMPOSE logs web --tail 100"
  exit 1
fi

echo ""
echo "Готово."
