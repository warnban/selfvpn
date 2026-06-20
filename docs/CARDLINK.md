# Cardlink — настройка онлайн-оплаты

Домен проекта: **https://daddyvpn.site**
VPS: `72.56.124.163`

Интеграция через **API** (`https://cardlink.link/api/v1/`), счёт создаётся методом `POST /bill/create`,
пользователь уводится на `link_page_url`, баланс зачисляется по postback на Result URL.

Freekassa и Cardlink сосуществуют. Активная касса выбирается переменной `PAYMENT_PROVIDER`.

---

## 1. URL для формы создания магазина в Cardlink

| Поле в кабинете Cardlink | Значение |
|--------------------------|----------|
| **URL магазина**         | `https://daddyvpn.site` |
| **Success URL**          | `https://daddyvpn.site/cardlink/success` |
| **Fail URL**             | `https://daddyvpn.site/cardlink/fail` |
| **Result URL**           | `https://daddyvpn.site/cardlink/result` |
| **Refund URL**           | `https://daddyvpn.site/cardlink/refund` |
| **Chargeback URL**       | `https://daddyvpn.site/cardlink/chargeback` |

Важно: домен магазина, Success URL и Fail URL должны быть на одном домене — у нас все на `daddyvpn.site`.

---

## 2. `.env` на сервере

```env
# Переключатель активной кассы: freekassa | cardlink
PAYMENT_PROVIDER=cardlink

CARDLINK_API_TOKEN=ваш_токен_со_страницы_API_интеграций
CARDLINK_SHOP_ID=идентификатор_магазина
```

- `CARDLINK_API_TOKEN` — токен со страницы «API интеграций» в кабинете Cardlink (формат `72|oBCB7Z...`).
- `CARDLINK_SHOP_ID` — `shop_id` созданного магазина (например `LXZv3R7Q8B`).
- Пока заявка не одобрена — оставьте `PAYMENT_PROVIDER=freekassa`. Переключите на `cardlink` после подключения.

```bash
cd /opt/selfvpn && git pull && bash deploy/update.sh
```

---

## 3. Как это работает

1. Пользователь в кабинете → «Пополнить» → срок и способ → «Оплатить».
2. Сервер создаёт счёт `POST /api/v1/bill/create` (`order_id` = id платежа в нашей БД) и редиректит на `link_page_url`.
3. После оплаты Cardlink:
   - редиректит пользователя POST-запросом на **Success/Fail URL** → показываем результат в кабинете;
   - шлёт **postback на Result URL** → проверяем подпись, зачисляем баланс, отвечаем `OK`.

`InvId` в ответах = `order_id` = id платежа в таблице `payments`.

---

## 4. Подписи (md5, верхний регистр)

| Где | Формула |
|-----|---------|
| Success / Fail / Result (payment) | `md5(OutSum:InvId:apiToken)` |
| Refund postback | `md5(Amount:Currency:BillId:PaymentId:Id:apiToken)` |
| Chargeback postback | `md5(BillId:PaymentId:Id:apiToken)` |

`apiToken` = `CARDLINK_API_TOKEN`. Проверка реализована в `bot/services/cardlink.py`.

---

## 5. Способы оплаты

Форма пополнения предлагает СБП (НСПК) и банковскую карту. Маппинг на Cardlink:

| Форма | Cardlink `payment_method` |
|-------|---------------------------|
| СБП   | `SBP` |
| Карта | `BANK_CARD` |

Если способ не передан — пользователь выбирает на странице Cardlink.

---

## 6. Проверка после подключения

1. В кабинете Cardlink сохраните магазин с URL из раздела 1.
2. Пропишите `.env`, выставьте `PAYMENT_PROVIDER=cardlink`, выполните `deploy/update.sh`.
3. Сделайте тестовое пополнение из кабинета.
4. Логи: `journalctl -u selfvpn-web -f` — ищите `Cardlink`.

| Симптом | Решение |
|---------|---------|
| `wrong sign` в логах Result | Токен в `.env` не совпадает с кабинетом Cardlink |
| Счёт не создаётся (`error=api`) | Проверьте `CARDLINK_API_TOKEN`, `CARDLINK_SHOP_ID`, белый список IP |
| Баланс не зачислился | Result URL должен отвечать `200`; проверьте подпись и статус `SUCCESS` |

---

## 7. Откат на Freekassa

Достаточно вернуть `PAYMENT_PROVIDER=freekassa` в `.env` и перезапустить веб —
маршруты `/cardlink/*` останутся, но оплата снова пойдёт через Freekassa.
