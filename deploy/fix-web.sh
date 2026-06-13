#!/bin/bash
# Быстрое восстановление веб-панели (обёртка над fix-502.sh)
set -e
cd "$(dirname "$0")"
bash fix-502.sh
