#!/usr/bin/env bash
# Remove Windows CRLF from shell scripts (run once after scp from Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

fix() {
  if [[ -f "$1" ]]; then
    sed -i 's/\r$//' "$1"
    echo "fixed: $1"
  fi
}

fix "$ROOT/android/scripts/build-merged-apk.sh"
fix "$ROOT/android/scripts/setup-wsl-build.sh"
fix "$ROOT/android/amnezia-client/deploy/build.sh"
fix "$ROOT/android/amnezia-client/client/android/gradlew"

find "$ROOT/android/amnezia-client/deploy" -name "*.sh" -print0 2>/dev/null \
  | while IFS= read -r -d '' f; do
    sed -i 's/\r$//' "$f"
  done

echo "Done."
