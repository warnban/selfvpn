#!/bin/bash
# Сборка лендинга в web/landing/ (обычно только на ПК разработчика).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/web/landing/index.html"

if [ -f "$OUT" ] && [ "${FORCE_LANDING_BUILD:-}" != "1" ]; then
  echo "Лендинг уже собран: web/landing/ (пропуск сборки)"
  exit 0
fi

if ! command -v npm >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
  echo "npm/node не найден — залей уже собранный web/landing/ из git"
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "Node.js $(node -v) слишком старый (нужен >=18). Собирай локально и пушь web/landing/"
  exit 1
fi

cd "$ROOT/landing"
npm ci 2>/dev/null || npm install
npm run build
echo "Лендинг собран: web/landing/"
