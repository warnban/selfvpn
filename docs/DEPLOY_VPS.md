# Деплой на второй VPS (РФ) — пошагово

Один VPS в **РФ** для: Telegram-бот + веб-кабинет + Amnezia Panel.  
NL VPS только для VPN (`amnezia-awg2`) — уже есть.

---

## Что купить

- **VPS в РФ**: Ubuntu 22.04/24.04, 1 GB RAM, 1 vCPU (~200–400 ₽/мес)
- Провайдеры: Timeweb, Selectel, Aeza, REG.RU и т.д.
- **Домен** (желательно): `vpn.твой-домен.ru` → A-запись на IP RU VPS

---

## Шаг 1 — Подключись к RU VPS

```bash
ssh root@IP_RU_VPS
apt update && apt upgrade -y
apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx ufw
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
```

---

## Шаг 2 — Загрузи проект

```bash
mkdir -p /opt/selfvpn
cd /opt/selfvpn
```

Скопируй файлы проекта (`C:\selfvpn`) на сервер через `scp`, WinSCP или git:

```bash
# если зальёшь в git:
git clone https://github.com/ТЫ/selfvpn.git /opt/selfvpn
cd /opt/selfvpn
cp .env.example .env
nano .env
```

Заполни `.env`:

```env
BOT_TOKEN=...
ADMIN_IDS=твой_telegram_id
DAILY_PRICE_RUB=5
TRIAL_DAYS=2
REFERRAL_BONUS_RUB=5

WEB_BASE_URL=https://vpn.твой-домен.ru
WEB_SECRET_KEY=длинная-случайная-строка-32+символов
ADMIN_WEB_PASSWORD=надёжный-пароль

PANEL_URL=http://127.0.0.1:5000
PANEL_API_TOKEN=получишь_на_шаге_4
PANEL_SERVER_ID=0
PANEL_PROTOCOL=awg2

PAYMENT_CARD=...
PAYMENT_BANK=...
PAYMENT_HOLDER=...
```

---

## Шаг 3 — Запусти бота и веб-кабинет

```bash
cd /opt/selfvpn
docker compose up -d --build
docker compose ps
docker compose logs -f web
docker compose logs -f bot
```

Проверка:
- `http://IP_RU_VPS:8080/admin/login` — админка
- Бот в Telegram — `/start`

---

## Шаг 4 — Amnezia Panel (управление VPN на NL)

На **том же RU VPS**:

```bash
cd /opt
git clone https://github.com/PRVTPRO/Amnezia-Web-Panel.git amnezia-panel
cd amnezia-panel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создай systemd-сервис `/etc/systemd/system/amnezia-panel.service`:

```ini
[Unit]
Description=Amnezia Web Panel
After=network.target

[Service]
WorkingDirectory=/opt/amnezia-panel
Environment=SECRET_KEY=ещё-одна-случайная-строка
ExecStart=/opt/amnezia-panel/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now amnezia-panel
```

1. SSH-туннель или проброс порта 5000 только на localhost (панель **не** светить в интернет)
2. Локально: `ssh -L 5000:127.0.0.1:5000 root@IP_RU_VPS`
3. Открой http://localhost:5000 → admin/admin → смени пароль
4. **Add Server** → IP **NL VPS**, root, SSH
5. **Settings → API Tokens** → скопируй в `.env` → `docker compose restart`

---

## Шаг 5 — Nginx + HTTPS

```bash
nano /etc/nginx/sites-available/selfvpn
```

```nginx
server {
    listen 80;
    server_name vpn.твой-домен.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 10M;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/selfvpn /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d vpn.твой-домен.ru
```

Обнови в `.env`:

```env
WEB_BASE_URL=https://vpn.твой-домен.ru
```

```bash
cd /opt/selfvpn && docker compose restart
```

---

## Шаг 6 — Финальная проверка

| Проверка | Ожидание |
|----------|----------|
| `/start` в боте | ссылка на личный кабинет |
| Кабинет в браузере | баланс, оплата, VPN |
| `/admin` | список пользователей, начисление |
| Начисление баланса | сообщение в Telegram |
| Пополнение (дни → сумма → скрин) | заявка в админке |
| Подключить VPN | `vpn://` работает в Amnezia |

---

## Подключить Cursor к серверу

1. Cursor → Remote SSH → `root@IP_RU_VPS`
2. Открой `/opt/selfvpn`
3. Я смогу править файлы и давать команды прямо на сервере

---

## Два сервера — итог

| Сервер | Где | Задача |
|--------|-----|--------|
| NL | Нидерланды | VPN `amnezia-awg2` |
| RU | Россия | Бот + кабинет + Panel |

Так быстрее и правильнее, чем переносить потом.
