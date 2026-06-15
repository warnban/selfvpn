# Сборка объединённого APK (Compose UI + Amnezia VPN)



Проект: `android/amnezia-client`  

Результат: один APK `site.daddyvpn.app` с вашим Compose UI и VPN-движком AWG2 внутри.



## Архитектура



```

DaddyVpnActivity (Compose UI, launcher)

        │ «Включить» + vpn:// ключ

        ▼

VpnBridge → AmneziaActivity (Qt + AWG2 VpnService)

        │ importConfigFromData + auto-connect (800 ms)

        ▼

AwgService (Android VpnService) — реальный туннель

```



Статус «подключено» в Compose берётся из `VpnStateStore` (не фейковый таймер).



## Что уже слито в форке



| Компонент | Файл |

|-----------|------|

| Compose launcher | `DaddyVpnActivity.kt` |

| VPN-движок | `AmneziaActivity.kt` + Qt/C++ |

| Мост vpn:// | `VpnBridge.kt` |

| Auto-connect после импорта | `coreSignalHandlers.cpp` |

| applicationId | `site.daddyvpn.app` |

| Брендинг | «Дядя Саня VPN» |



UI-only проект для быстрой разработки: `android/daddyvpn-app/` (без Qt).



---



## Быстрый старт (Windows + WSL Ubuntu)



### Шаг 0 — проверка



```powershell

wsl --list --verbose

# Нужен дистрибутив Ubuntu (Stopped или Running)

```



### Шаг 1 — установка пакетов в WSL (один раз)



```powershell

wsl -d Ubuntu bash android/scripts/setup-wsl-build.sh

```



Устанавливает: OpenJDK 17, cmake, ninja, conan, git submodules.



### Шаг 2 — Qt 6 + Android SDK (один раз, вручную)



**Qt 6.10+** — [Qt Online Installer](https://www.qt.io/download-open-source):

- Qt 6.x → Android → arm64-v8a

- Qt 5 Compatibility Module

- Qt Remote Objects



**Android SDK** — Android Studio или commandline-tools:

- SDK Platform 35

- NDK r27+ (например `27.2.12479018`)

- CMake 3.22+



Добавьте в `~/.bashrc` внутри WSL Ubuntu (пути под себя):



```bash

export QT_INSTALL_DIR="$HOME/Qt"

export QT_ROOT_PATH="$HOME/Qt/6.10.0"

export QT_HOST_PATH="$HOME/Qt/6.10.0/gcc_64"

export ANDROID_HOME="$HOME/Android/Sdk"

export ANDROID_SDK_ROOT="$ANDROID_HOME"

export ANDROID_NDK_ROOT="$ANDROID_HOME/ndk/27.2.12479018"

export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"

export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"

```



Перезапустите WSL: `wsl --shutdown`, затем снова откройте Ubuntu.



### Шаг 3 — брендинг + сборка



```powershell

cd C:\selfvpn\android\scripts

.\build-merged-apk.ps1

```



Или полностью в WSL:



```bash

cd /mnt/c/selfvpn

bash android/scripts/build-merged-apk.sh

```



Первая сборка: **30–90 минут** (Qt + native libs).  

APK: `android/daddyvpn-merged-debug.apk`



Установка на телефон:



```powershell

adb install -r C:\selfvpn\android\daddyvpn-merged-debug.apk

```



### Шаг 4 — тест



1. Откройте «Дядя Саня VPN» (ваш merged APK).

2. Вставьте ключ `vpn://…` из бота.

3. Нажмите **Включить**.

4. Подтвердите разрешение VPN (если система спросит).

5. В статус-баре появится иконка VPN; UI покажет «ЗАЩИЩЕНО».



> AmneziaActivity (Qt) может мелькнуть на секунду — это нормально: движок импортирует ключ и поднимает туннель. Compose UI остаётся главным экраном.



---



## Синхронизация UI из daddyvpn-app



После правок в `daddyvpn-app`:



```powershell

.\android\scripts\sync-ui-to-amnezia.ps1

```



Автосинх: `Color.kt`, `Theme.kt`, `HomeScreen.kt`, `KeySheet.kt`, `KeyStore.kt`.  

Вручную в форке: `DaddyVpnActivity`, `MainViewModel`, `VpnBridge`, `AndroidManifest`.



---



## Сборка только arm64 (быстрее)



```powershell

.\build-merged-apk.ps1 -Abi arm64-v8a

```



Другие ABI: `armeabi-v7a`, `x86_64` (эмулятор).



---



## Troubleshooting



| Проблема | Решение |

|----------|---------|

| `Qt not found` | Проверьте `QT_ROOT_PATH` в `~/.bashrc` |

| `ANDROID_NDK_ROOT` пуст | Установите NDK в SDK Manager |

| `git submodule` ошибки | `cd amnezia-client && git submodule update --init --recursive` |

| `gradlew: not found` | `aqt`-Qt без Gradle-шаблонов. Запустите `bash android/scripts/fix-crlf.sh`, затем сборку заново. Скрипт сам копирует wrapper. |
| Gradle после Qt | Открывайте `deploy/build/client/android-build`, не `client/android` |

| VPN не подключается | Проверьте ключ `vpn://` в Amnezia logcat: `adb logcat \| grep -i amnezia` |

| Две вкладки / пустой экран | Установите merged APK, не UI-only `daddyvpn-app` |



---



## GPL



Форк Amnezia — лицензия GPL-3.0. Публикуйте изменения форка в открытом репозитории.


