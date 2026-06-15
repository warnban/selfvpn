#!/bin/bash
# Проверка доступности SMTP с сервера
set -e
cd /opt/selfvpn

HOST="${SMTP_HOST:-smtp.timeweb.ru}"
echo "=== Проверка SMTP: $HOST ==="
echo ""

for PORT in 465 587 25; do
  echo -n "Порт $PORT: "
  if timeout 5 bash -c "echo >/dev/tcp/$HOST/$PORT" 2>/dev/null; then
    echo "ДОСТУПЕН"
  else
    echo "недоступен (таймаут или блокировка)"
  fi
done

echo ""
echo "=== Настройки из .env ==="
grep -E '^SMTP_' .env 2>/dev/null | sed 's/SMTP_PASSWORD=.*/SMTP_PASSWORD=***hidden***/' || echo "SMTP не задан"

echo ""
echo "=== Тест отправки (если venv есть) ==="
if [ -x ./venv/bin/python ]; then
  ./venv/bin/python - <<'PY'
import asyncio
import os
from pathlib import Path

# load .env manually for test
for line in Path(".env").read_text().splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

async def main():
    from bot.services.email import send_email
    to = os.environ.get("SMTP_TEST_TO", os.environ.get("SMTP_USER", ""))
    if not to:
        print("Задай SMTP_TEST_TO=your@email.ru для тестовой отправки")
        return
    ok = await send_email(to, "SelfVPN SMTP test", "<p>Тест SMTP с сервера</p>")
    print("OK" if ok else "FAIL")

asyncio.run(main())
PY
else
  echo "venv не найден"
fi

echo ""
echo "Если порты 465/587 недоступны — хостинг блокирует исходящую почту."
echo "Варианты: порт 587, другой SMTP (Resend/SendGrid), или VPS в РФ у Timeweb."
