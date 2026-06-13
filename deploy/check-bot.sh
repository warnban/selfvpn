#!/bin/bash
# Быстрая диагностика бота на сервере: bash deploy/check-bot.sh

set -e
cd /opt/selfvpn

echo "=== docker-compose ps ==="
docker-compose ps

echo ""
echo "=== bot logs (last 40 lines) ==="
docker-compose logs bot --tail 40

echo ""
echo "=== BOT_TOKEN set? (first 10 chars only) ==="
docker-compose exec -T bot sh -c 'echo ${BOT_TOKEN:0:10}...'

echo ""
echo "=== Telegram API getMe ==="
TOKEN=$(grep '^BOT_TOKEN=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | head -c 300
echo ""

echo ""
echo "=== deleteWebhook ==="
curl -s "https://api.telegram.org/bot${TOKEN}/deleteWebhook"
echo ""
