# Деплой на твой VPS: 72.56.124.163 (Ubuntu 22.04)

## Что нужно заранее

1. **BOT_TOKEN** — от @BotFather  
2. **ADMIN_IDS** — твой Telegram ID (@userinfobot)  
3. **Пароль root** от VPS (или SSH-ключ)  
4. **Реквизиты карты** для оплаты  

---

## Шаг 1 — Загрузи проект на сервер

### Вариант A: с Windows (PowerShell)

```powershell
scp -r C:\selfvpn root@72.56.124.163:/opt/selfvpn
```

### Вариант B: прямо на сервере (если нет scp)

```bash
ssh root@72.56.124.163
apt install -y git
mkdir -p /opt/selfvpn
```

Потом залей файлы через WinSCP в `/opt/selfvpn` или сделай git push и clone.

---

## Шаг 2 — Настрой .env на сервере

```bash
ssh root@72.56.124.163
cd /opt/selfvpn
cp .env.example .env
nano .env
```

Заполни **обязательно**:

```env
BOT_TOKEN=7123456789:AAH...
ADMIN_IDS=123456789

DAILY_PRICE_RUB=5
TRIAL_DAYS=2
REFERRAL_BONUS_RUB=5

WEB_BASE_URL=http://72.56.124.163:8080
WEB_SECRET_KEY=придумай-длинную-случайную-строку-32-символа
ADMIN_WEB_PASSWORD=пароль-для-входа-в-админку

PAYMENT_CARD=2200 0000 0000 0000
PAYMENT_BANK=Сбербанк
PAYMENT_HOLDER=Имя Ф.

PANEL_URL=http://172.17.0.1:5000
PANEL_API_TOKEN=
PANEL_SERVER_ID=0
PANEL_PROTOCOL=awg2
```

> `PANEL_API_TOKEN` заполнишь после шага 4.

---

## Шаг 3 — Установка одной командой

```bash
cd /opt/selfvpn
chmod +x deploy/install.sh
bash deploy/install.sh
```

Или вручную:

```bash
cd /opt/selfvpn
docker compose up -d --build
docker compose ps
docker compose logs -f
```

---

## Шаг 4 — Amnezia Panel + NL VPN

**На своём Windows** открой второй терминал:

```powershell
ssh -L 5000:127.0.0.1:5000 root@72.56.124.163
```

В браузере: http://localhost:5000  
Логин: `admin` / `admin` → **сразу смени пароль**

1. **Servers → Add Server**  
   - Host: IP твоего **NL VPN** сервера  
   - User: `root`  
   - Password / SSH key  

2. Дождись проверки — должен появиться **AmneziaWG 2.0**

3. **Settings → API Tokens → Create** → скопируй `awp_...`

4. На VPS:

```bash
nano /opt/selfvpn/.env
# PANEL_API_TOKEN=awp_...
# PANEL_URL=http://host.docker.internal:5000
```

Если бот не достучится до panel, попробуй:

```env
PANEL_URL=http://172.17.0.1:5000
```

```bash
cd /opt/selfvpn && docker compose restart
```

---

## Шаг 5 — Проверка

| Действие | URL / команда |
|----------|----------------|
| Админка | http://72.56.124.163:8080/admin/login |
| Бот | `/start` в Telegram |
| Логи | `docker compose logs -f bot` |

---

## Шаг 6 — Домен + HTTPS (позже)

Когда купишь домен — напиши, настроим Nginx + Let's Encrypt.

---

## Cursor Remote SSH

1. Cursor → Remote SSH → `root@72.56.124.163`  
2. Open Folder → `/opt/selfvpn`  
3. Пиши «продолжаем деплой» — смогу править файлы на сервере
