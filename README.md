# SelfVPN

Telegram-бот + веб-кабинет для продажи Amnezia VPN.

## Возможности

- Пробный баланс на 2 дня при регистрации
- Тариф ₽/сутки, ежедневное списание
- Реферальная система
- Оплата: выбор **количества дней** → расчёт суммы → перевод → скрин
- **Личный кабинет** в браузере (без Telegram)
- **Админ-панель**: пользователи, начисление баланса, модерация оплат
- Уведомления в Telegram при начислении / одобрении оплаты

## Документация

- [Пошаговая настройка](docs/SETUP.md)
- [Деплой на второй VPS (РФ)](docs/DEPLOY_VPS.md)

## Локальный запуск (Windows)

```powershell
cd C:\selfvpn
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# заполни .env

# Терминал 1 — веб
uvicorn web.app:app --reload --port 8080

# Терминал 2 — бот
python -m bot.main
```

- Кабинет: http://127.0.0.1:8080/cabinet/TOKEN (из бота после /start)
- Админка: http://127.0.0.1:8080/admin/login

## Docker (VPS)

```bash
docker compose up -d --build
```
