# Freekassa — настройка автооплаты в веб-кабинете

Домен проекта: **https://daddyvpn.site**  
VPS: `72.56.124.163`

## 1. DNS (в панели регистратора домена)

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `@` | `72.56.124.163` |
| A | `www` | `72.56.124.163` |

Подождите 5–30 минут, пока DNS обновится.

## 2. HTTPS на сервере

```bash
ssh root@72.56.124.163
cd /opt/selfvpn
chmod +x deploy/setup-domain.sh
bash deploy/setup-domain.sh
```

Или вручную — конфиг: `deploy/nginx-daddyvpn.site.conf`

## 3. `.env` на сервере

```env
WEB_BASE_URL=https://daddyvpn.site

FREEKASSA_MERCHANT_ID=ваш_id
FREEKASSA_SECRET_1=секретное-слово-1
FREEKASSA_SECRET_2=секретное-слово-2
```

```bash
cd /opt/selfvpn && docker compose restart
```

---

## Что вписать в форму Freekassa

| Поле | Значение | Метод |
|------|----------|-------|
| **URL сайта** | `https://daddyvpn.site` | — |
| **Секретное слово 1** | → `FREEKASSA_SECRET_1` в `.env` | — |
| **Секретное слово 2** | → `FREEKASSA_SECRET_2` в `.env` | — |
| **URL оповещения** | `https://daddyvpn.site/payment/notify` | **GET** |
| **URL успешной оплаты** | `https://daddyvpn.site/payment/success` | GET |
| **URL неудачи** | `https://daddyvpn.site/payment/fail` | GET |

---

## Как это работает

1. Пользователь в веб-кабинете → «Пополнить» → выбирает дни → «Оплатить картой»
2. Редирект на `pay.fk.money`
3. После оплаты Freekassa бьёт в `/payment/notify` → бот зачисляет баланс → отвечает `YES`
4. Пользователь возвращается на `/payment/success` → кабинет с сообщением «Баланс пополнен»

Оплата в **Telegram-боте** по-прежнему ручная (перевод + скрин), если не добавите туда отдельно.

---

## Проверка

1. В Freekassa нажмите **«Сохранить и проверить»** — должен открыться notify URL (не 404)
2. Включите **тестовый режим** в Freekassa и сделайте тестовый платёж из кабинета
3. Логи: `docker compose logs -f web`

---

## Частые проблемы

| Симптом | Решение |
|---------|---------|
| «Сохранить и проверить» не проходит | Нет HTTPS или домен не указывает на VPS |
| Баланс не зачислился | Проверьте `FREEKASSA_SECRET_2`, метод GET, логи web |
| `wrong sign` в логах | Секретное слово 2 не совпадает с личным кабинетом |
| `hacking attempt!` | Запрос не с IP Freekassa (проверяйте через реальный платёж, не вручную с браузера) |
