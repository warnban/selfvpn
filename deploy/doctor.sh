#!/bin/bash
# Диагностика: какой бот запущен и какой код на диске.
set -e
cd /opt/selfvpn

echo "=== Git ==="
git log -1 --oneline 2>/dev/null || echo "нет git"
grep -n "ADM PANEL" bot/keyboards/main.py || echo "НЕТ admin-кнопок в коде на диске"
test -f bot/handlers/admin.py && echo "admin.py: есть" || echo "admin.py: НЕТ"

echo ""
echo "=== ADMIN_IDS ==="
grep '^ADMIN_IDS=' .env || echo "ADMIN_IDS не задан"

echo ""
echo "=== Кто запущен ==="
echo -n "systemd selfvpn-bot: "
systemctl is-active selfvpn-bot 2>/dev/null || echo "не установлен/не активен"
echo -n "docker bot: "
docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null | grep selfvpn_bot || echo "нет контейнера"

echo ""
echo "=== Процессы bot.main ==="
pgrep -af "bot\.main" || echo "нет процессов"

echo ""
echo "=== Последние логи (docker) ==="
docker logs selfvpn_bot_1 --tail 15 2>/dev/null || echo "контейнер bot не запущен"

echo ""
echo "=== Последние логи (systemd) ==="
journalctl -u selfvpn-bot -n 15 --no-pager 2>/dev/null || echo "нет systemd-сервиса"
