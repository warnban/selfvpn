#!/usr/bin/env bash
# One-time setup for building DaddyVPN merged APK (Compose UI + Amnezia VPN) in WSL Ubuntu.
set -euo pipefail

echo "=== DaddyVPN: WSL build environment setup ==="

sudo apt-get update
sudo apt-get install -y \
  openjdk-17-jdk \
  git \
  cmake \
  ninja-build \
  python3 \
  python3-pip \
  python3-venv \
  libgl1-mesa-dev \
  libxkbcommon-dev \
  libxcb-*-dev \
  libx11-xcb-dev \
  libxrandr-dev \
  libxi-dev \
  libfontconfig1-dev \
  libfreetype6-dev \
  libssl-dev \
  pkg-config \
  unzip \
  curl

# Conan (Amnezia dependency manager)
if ! command -v conan >/dev/null 2>&1; then
  python3 -m pip install --user conan
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  export PATH="$HOME/.local/bin:$PATH"
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AMNEZIA_ROOT="$REPO_ROOT/android/amnezia-client"

if [[ ! -d "$AMNEZIA_ROOT/.git" ]]; then
  echo "Cloning amnezia-client..."
  git clone --depth 1 https://github.com/amnezia-vpn/amnezia-client.git "$AMNEZIA_ROOT"
fi

cd "$AMNEZIA_ROOT"
git submodule update --init --recursive

echo ""
echo "=== Manual steps (one time) ==="
echo ""
echo "1. Install Qt 6.10+ with Android modules via Qt Online Installer:"
echo "   https://www.qt.io/download-open-source"
echo "   Components: Qt 6.x for Android (arm64-v8a), Qt 5 Compatibility, Qt Remote Objects"
echo "   Typical path: ~/Qt/6.10.0/"
echo ""
echo "2. Install Android SDK + NDK (via Android Studio or sdkmanager):"
echo "   SDK:  ~/Android/Sdk"
echo "   NDK:  ~/Android/Sdk/ndk/<version>"
echo ""
echo "3. Add to ~/.bashrc (adjust paths):"
cat <<'ENV'

export QT_INSTALL_DIR="$HOME/Qt"
export QT_ROOT_PATH="$HOME/Qt/6.10.0"
export QT_HOST_PATH="$HOME/Qt/6.10.0/gcc_64"
export ANDROID_HOME="$HOME/Android/Sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_NDK_ROOT="$ANDROID_HOME/ndk/27.2.12479018"
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"

ENV
echo ""
echo "4. Apply DaddyVPN branding:"
echo "   pwsh.exe -File android/scripts/apply-branding.ps1"
echo ""
echo "5. Build merged APK:"
echo "   bash android/scripts/build-merged-apk.sh"
echo ""
echo "Setup packages installed. Configure Qt + Android SDK, then run build-merged-apk.sh"
