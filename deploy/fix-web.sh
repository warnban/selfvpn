#!/bin/bash
# Быстрое восстановление веб-панели
set -e
cd /opt/selfvpn

echo "=== Статус ==="
docker-compose ps
echo ""
docker logs $(docker ps -aq --filter "name=web" | head -1) --tail 30 2>/dev/null || echo "Web-контейнер не найден"

echo ""
echo "=== Проверка файлов ==="
ls -la web/static/css/app.css 2>/dev/null || echo "ОТСУТСТВУЕТ: web/static/css/app.css — залей с ПК!"
ls -la web/templates/base.html 2>/dev/null || echo "ОТСУТСТВУЕТ: web/templates/"

echo ""
echo "=== Пересборка web ==="
docker-compose up -d --build web
sleep 3
docker-compose ps

echo ""
echo "=== Проверка порта 8080 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8080/admin/login || echo "FAIL"
