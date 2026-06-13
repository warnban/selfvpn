#!/bin/bash
# Обновление selfvpn с GitHub на сервере.
# Использование: cd /opt/selfvpn && bash deploy/update.sh

set -e
cd "$(dirname "$0")/.."

echo "==> git pull"
git pull --ff-only

echo "==> restart containers (код монтируется как volume)"
docker-compose restart bot web

echo "==> status"
docker-compose ps

echo "Готово."
