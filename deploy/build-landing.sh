#!/bin/bash
# Сборка лендинга в web/landing/
set -e
cd "$(dirname "$0")/../landing"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm не найден — установь Node.js или залей уже собранный web/landing/"
  exit 1
fi

npm ci 2>/dev/null || npm install
npm run build
echo "Лендинг собран: web/landing/"
