#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${EUID} -eq 0 ]]; then
    exec "$ROOT_DIR/install.sh" --no-apt "$@"
else
    exec sudo "$ROOT_DIR/install.sh" --no-apt "$@"
fi
