#!/usr/bin/env bash
set -euo pipefail
HOST=${1:?usage: install-node.sh user@host}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cargo build --release -p qdw-node
ssh "$HOST" 'mkdir -p ~/.local/bin ~/.config/qdw-node ~/.config/systemd/user'
scp "$ROOT/target/release/qdw-node" "$HOST:~/.local/bin/qdw-node"
scp "$ROOT/config/node.example.toml" "$HOST:~/.config/qdw-node/config.toml"
scp "$ROOT/systemd/qdw-node.service" "$HOST:~/.config/systemd/user/qdw-node.service"
ssh "$HOST" 'systemctl --user daemon-reload && systemctl --user enable --now qdw-node && systemctl --user status --no-pager qdw-node'
echo "Node installed loopback-only. Add it to Workbench config and connect through SSH forwarding."
