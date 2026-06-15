# DaddyVPN Android

## Два проекта

| Папка | Назначение | Сборка |
|-------|------------|--------|
| `daddyvpn-app/` | UI-only, для разработки в Android Studio | ✅ Сейчас |
| `amnezia-client/client/android/` | UI + VPN (форк Amnezia) | ⚙️ Нужен Qt build |

**Слияние UI → форк выполнено в коде.** Подробно: [docs/MERGE.md](docs/MERGE.md)

## Быстрый старт (UI)

Откройте **`android/daddyvpn-app`** в Android Studio → Run.

Ключ `vpn://` из бота → 🔑 → **Включить**.

После полного APK (Qt) «Включить» откроет VPN **внутри того же приложения**.

```
android/
  daddyvpn-app/      ← Jetpack Compose UI (site.daddyvpn.app)
  amnezia-client/    ← форк Amnezia (git clone, не в git)
  figma.config.json  ← ссылка и токены дизайна
  scripts/           ← скрипты брендинга форка
```

## Как пользоваться (без логина)

1. Получите ключ `vpn://…` в Telegram-боте или личном кабинете (вкладка «Ключ» у устройства).
2. Откройте приложение и вставьте ключ (иконка 🔑) **или** нажмите на ссылку `vpn://` — приложение перехватит её само.
3. Нажмите **Включить**.

Баланс, оплата и новые устройства — в боте / веб-кабинете. Приложение только подключает VPN по ключу.

### Способы передать ключ

| Способ | Как |
|--------|-----|
| Вставить | 🔑 в шапке → вставить `vpn://…` → Сохранить |
| Ссылка | Тап по `vpn://` в Telegram → «Открыть в Дядя Саня VPN» |
| «Поделиться» | Share → выбрать приложение (текст с `vpn://`) |

## Mobile API (опционально)

REST API в `web/mobile_api.py` — для будущих фич (баланс в приложении). **Для подключения не нужен.**

### Сборка

1. Откройте `android/daddyvpn-app` в **Android Studio Ladybug+**
2. Sync Gradle → Run

```powershell
cd C:\selfvpn\android
git clone --depth 1 https://github.com/amnezia-vpn/amnezia-client.git amnezia-client
```

## Форк Amnezia (полный VPN в одном APK)

Compose UI + VPN AWG2 в одном `site.daddyvpn.app`. Подробная инструкция: **[docs/MERGE.md](docs/MERGE.md)**.

```powershell
# 1. Один раз: пакеты в WSL Ubuntu
wsl -d Ubuntu bash android/scripts/setup-wsl-build.sh

# 2. Установить Qt 6 + Android SDK/NDK (см. MERGE.md)

# 3. Сборка merged APK
cd android\scripts
.\build-merged-apk.ps1
```

APK: `android/daddyvpn-merged-debug.apk` — VPN работает **внутри** приложения, Amnezia из Store не нужна.

## Дизайн (Figma)

Токены из макета:

- Фон `#0a0d14`, акцент `#00d4a1`
- Шрифты: Inter (UI), monospace (таймер/статы)
- Экран: power button, сервер, таймер сессии, stats panel, bottom nav

Реализовано в `ui/screens/HomeScreen.kt` по `App.tsx` из Figma Make.

## Roadmap

- [ ] Реальный ping/скорость из VPN-сервиса Amnezia
- [ ] Экран «Серверы» / «Настройки» из bottom nav
- [ ] RuStore + Play Store публикация
