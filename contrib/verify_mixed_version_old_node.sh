#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${MIXED_VERSION_LOG_DIR:-$ROOT_DIR/test-logs/customized_halving_old_node}"

export BITCOIND="${BITCOIND:-$ROOT_DIR/src/rincoind}"
export BITCOINCLI="${BITCOINCLI:-$ROOT_DIR/src/rincoin-cli}"
export OLD_RINCOIND="${OLD_RINCOIND:-/usr/local/bin/rincoind}"
export OLD_RINCOINCLI="${OLD_RINCOINCLI:-/usr/local/bin/rincoin-cli}"

mkdir -p "$(dirname "$LOG_DIR")"
rm -rf "$LOG_DIR"

cd "$ROOT_DIR"
. .venv/bin/activate

PYTHONUNBUFFERED=1 python3 test/functional/feature_customized_halving_old_node.py \
  --nocleanup \
  --tmpdir="$LOG_DIR"

printf '\nMixed-version logs preserved under: %s\n' "$LOG_DIR"
