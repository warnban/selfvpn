#!/usr/bin/env bash
# Build DaddyVPN merged APK: Compose UI + in-app Amnezia AWG2 VPN engine.
#
# Uses Amnezia's Android flow (deploy/build_android.sh):
#   1. qt-cmake with QT_NO_GLOBAL_APK_TARGET_PART_OF_ALL=ON (native only)
#   2. androiddeployqt (package, skip gradle)
#   3. gradlew assembleDebug/Release
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AMNEZIA_ROOT="$REPO_ROOT/android/amnezia-client"
BUILD_DIR="$AMNEZIA_ROOT/deploy/build"
OUT_APP_DIR="$BUILD_DIR/client"
ANDROID_SRC="$AMNEZIA_ROOT/client/android"
ANDROID_BUILD="$OUT_APP_DIR/android-build"

ABI="${ABI:-arm64-v8a}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
ANDROID_BUILD_PLATFORM="${ANDROID_BUILD_PLATFORM:-android-35}"

require_var() {
  if [[ -z "${!1:-}" ]]; then
    echo "ERROR: $1 is not set. Configure ~/.bashrc (QT_ROOT_PATH, QT_HOST_PATH, ANDROID_HOME, ...)"
    exit 1
  fi
}

qt_android_suffix() {
  case "$1" in
    armeabi-v7a) echo "armv7" ;;
    arm64-v8a)   echo "arm64_v8a" ;;
    x86)         echo "x86" ;;
    x86_64)      echo "x86_64" ;;
    *) echo "Unsupported ABI: $1" >&2; exit 1 ;;
  esac
}

gradle_build_type() {
  if [[ "${1,,}" == "debug" ]]; then
    echo "debug"
  else
    echo "release"
  fi
}

fix_crlf() {
  local f
  for f in "$@"; do
    if [[ -f "$f" ]] && grep -q $'\r' "$f" 2>/dev/null; then
      sed -i 's/\r$//' "$f"
    fi
  done
}

# aqt-installed Qt often lacks src/3rdparty/gradle; androiddeployqt needs it.
seed_qt_gradle_templates() {
  local qt_gradle
  for abi_dir in "$QT_ROOT_PATH"/android_*; do
    [[ -d "$abi_dir" ]] || continue
    qt_gradle="$abi_dir/src/3rdparty/gradle"
    if [[ -x "$qt_gradle/gradlew" ]]; then
      continue
    fi
    echo "Seeding Gradle wrapper in $qt_gradle"
    mkdir -p "$qt_gradle/gradle"
    cp "$ANDROID_SRC/gradlew" "$qt_gradle/"
    cp -r "$ANDROID_SRC/gradle/wrapper" "$qt_gradle/gradle/"
    fix_crlf "$qt_gradle/gradlew"
    chmod +x "$qt_gradle/gradlew"
  done
}

ensure_android_gradle() {
  if [[ -x "$ANDROID_BUILD/gradlew" ]]; then
    fix_crlf "$ANDROID_BUILD/gradlew"
    chmod +x "$ANDROID_BUILD/gradlew"
    return
  fi
  echo "Copying Gradle wrapper into $ANDROID_BUILD"
  cp "$ANDROID_SRC/gradlew" "$ANDROID_BUILD/"
  cp -r "$ANDROID_SRC/gradle" "$ANDROID_BUILD/"
  fix_crlf "$ANDROID_BUILD/gradlew"
  chmod +x "$ANDROID_BUILD/gradlew"
}

require_var QT_ROOT_PATH
require_var QT_HOST_PATH
require_var ANDROID_HOME
require_var ANDROID_NDK_ROOT
require_var JAVA_HOME

echo "=== DaddyVPN merged APK build ==="
echo "Repo:     $REPO_ROOT"
echo "Amnezia:  $AMNEZIA_ROOT"
echo "ABI:      $ABI"
echo "Type:     $BUILD_TYPE"
echo "Platform: $ANDROID_BUILD_PLATFORM"
echo ""

if [[ ! -d "$AMNEZIA_ROOT/.git" ]]; then
  echo "ERROR: amnezia-client not found at $AMNEZIA_ROOT"
  exit 1
fi

if [[ ! -x "$ANDROID_SRC/gradlew" ]]; then
  echo "ERROR: $ANDROID_SRC/gradlew not found"
  exit 1
fi

cd "$AMNEZIA_ROOT"
if [[ ! -f client/3rd/qtkeychain/.git ]]; then
  echo "Initializing git submodules..."
  git submodule update --init --recursive
fi

fix_crlf "$ANDROID_SRC/gradlew" "$AMNEZIA_ROOT/deploy/build.sh"
seed_qt_gradle_templates

export QT_INSTALL_DIR="${QT_INSTALL_DIR:-$(dirname "$QT_ROOT_PATH")}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"

QT_SUFFIX="$(qt_android_suffix "$ABI")"
QT_BIN_DIR="$QT_ROOT_PATH/android_${QT_SUFFIX}/bin"
GRADLE_TYPE="$(gradle_build_type "$BUILD_TYPE")"
GRADLE_TASK="assemble${BUILD_TYPE^}"

if [[ ! -x "$QT_BIN_DIR/qt-cmake" ]]; then
  echo "ERROR: qt-cmake not found at $QT_BIN_DIR/qt-cmake"
  exit 1
fi

mkdir -p "$BUILD_DIR"

echo "Configuring with qt-cmake..."
"$QT_BIN_DIR/qt-cmake" -S "$AMNEZIA_ROOT" -B "$BUILD_DIR" \
  -DQT_NO_GLOBAL_APK_TARGET_PART_OF_ALL=ON \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DQT_ANDROID_ABIS="$ABI"

echo ""
echo "Building Qt + native VPN stack (30-60+ min on first run)..."
cmake --build "$BUILD_DIR" --config "$BUILD_TYPE"

DEPLOY_JSON="$OUT_APP_DIR/android-AmneziaVPN-deployment-settings.json"
if [[ ! -f "$DEPLOY_JSON" ]]; then
  echo "ERROR: $DEPLOY_JSON not found after native build"
  exit 1
fi

echo ""
echo "Running androiddeployqt..."
deployqt_opts=(--input "$DEPLOY_JSON" --output "$ANDROID_BUILD" --android-platform "$ANDROID_BUILD_PLATFORM")
if [[ "$GRADLE_TYPE" == "release" ]]; then
  deployqt_opts+=(--release)
else
  deployqt_opts+=(--debug)
fi

export ANDROIDDEPLOYQT_RUN=1
"$QT_HOST_PATH/bin/androiddeployqt" "${deployqt_opts[@]}"

ensure_android_gradle

echo ""
echo "Gradle $GRADLE_TASK..."
"$ANDROID_BUILD/gradlew" \
  --project-dir "$ANDROID_BUILD" \
  -DexplicitRun=1 \
  "$GRADLE_TASK" \
  --no-daemon

APK=$(find "$ANDROID_BUILD/build/outputs/apk/$GRADLE_TYPE" -name "*.apk" 2>/dev/null | head -1)
if [[ -z "$APK" ]]; then
  APK=$(find "$ANDROID_BUILD/app/build/outputs/apk/$GRADLE_TYPE" -name "*.apk" 2>/dev/null | head -1)
fi

if [[ -n "$APK" ]]; then
  OUT="$REPO_ROOT/android/daddyvpn-merged-${GRADLE_TYPE}.apk"
  cp "$APK" "$OUT"
  echo ""
  echo "SUCCESS: $OUT"
  echo "Install: adb install -r \"$OUT\""
else
  echo "Build finished but APK not found under $ANDROID_BUILD/build/outputs/apk/$GRADLE_TYPE"
  exit 1
fi
