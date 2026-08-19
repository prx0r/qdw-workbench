#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
command -v cargo >/dev/null || { echo "Rust/cargo required" >&2; exit 2; }
command -v npm >/dev/null || { echo "Node/npm required" >&2; exit 2; }
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install -e "$ROOT/integrations/qdw_bridge"
npm install --prefix "$ROOT/apps/desktop/web"
mkdir -p "$HOME/.config/qdw-workbench" "$HOME/.config/qdw-node"
[ -e "$HOME/.config/qdw-workbench/config.toml" ] || cp "$ROOT/config/config.example.toml" "$HOME/.config/qdw-workbench/config.toml"
[ -e "$HOME/.config/qdw-node/config.toml" ] || cp "$ROOT/config/node.example.toml" "$HOME/.config/qdw-node/config.toml"
echo "Bootstrap complete. Edit ~/.config/qdw-workbench/config.toml then run scripts/dev.sh"
