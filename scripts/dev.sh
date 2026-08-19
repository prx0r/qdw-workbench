#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
trap 'kill 0 2>/dev/null || true' EXIT
cargo run -p qdw-node -- --config "$HOME/.config/qdw-node/config.toml" &
cd "$ROOT/apps/desktop/src-tauri"
cargo tauri dev
