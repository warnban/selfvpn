#!/bin/bash
# Первичная настройка git на сервере (один раз).
# Использование:
#   bash deploy/setup-git-server.sh https://github.com/USER/selfvpn.git

set -e
REPO_URL="$1"
TARGET="/opt/selfvpn"

if [ -z "$REPO_URL" ]; then
  echo "Укажи URL репозитория:"
  echo "  bash deploy/setup-git-server.sh https://github.com/USER/selfvpn.git"
  exit 1
fi

if [ -f "$TARGET/.env" ]; then
  echo "Сохраняю .env и data..."
  cp "$TARGET/.env" /tmp/selfvpn.env.bak
  cp -a "$TARGET/data" /tmp/selfvpn-data.bak 2>/dev/null || true
fi

if [ -d "$TARGET/.git" ]; then
  echo "Git уже инициализирован в $TARGET"
  cd "$TARGET"
  git remote set-url origin "$REPO_URL" 2>/dev/null || git remote add origin "$REPO_URL"
  git fetch origin
  git checkout -B main origin/main 2>/dev/null || git checkout -B master origin/master
  git pull --ff-only
else
  echo "Клонирую в $TARGET..."
  rm -rf "$TARGET.new"
  git clone "$REPO_URL" "$TARGET.new"
  if [ -d "$TARGET" ]; then
    mv "$TARGET" "${TARGET}.old.$(date +%s)"
  fi
  mv "$TARGET.new" "$TARGET"
fi

if [ -f /tmp/selfvpn.env.bak ]; then
  cp /tmp/selfvpn.env.bak "$TARGET/.env"
  echo ".env восстановлен"
fi
if [ -d /tmp/selfvpn-data.bak ]; then
  rm -rf "$TARGET/data"
  cp -a /tmp/selfvpn-data.bak "$TARGET/data"
  echo "data/ восстановлена"
fi

cd "$TARGET"
docker-compose down
docker-compose up -d

echo "Готово. Проверь: docker-compose ps"
