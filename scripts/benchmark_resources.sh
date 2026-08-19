#!/usr/bin/env bash
set -euo pipefail
BIN=${1:-target/release/qdw-node}
CONFIG=${2:-$HOME/.config/qdw-node/config.toml}
OUT=${3:-build/resource-measurement.json}
mkdir -p "$(dirname "$OUT")"
"$BIN" --config "$CONFIG" >/tmp/qdw-node-bench.log 2>&1 & pid=$!
trap 'kill $pid 2>/dev/null || true' EXIT
sleep 3
rss=0
for _ in $(seq 1 20); do r=$(awk '/VmRSS/{print $2*1024}' /proc/$pid/status 2>/dev/null || echo 0); [ "$r" -gt "$rss" ] && rss=$r; sleep .5; done
python3 -c 'import json,platform,sys,time; json.dump({"observed_at":time.time(),"platform":platform.platform(),"peak_sampled_rss_bytes":int(sys.argv[2]),"method":"/proc/PID/status VmRSS sampled 20x/0.5s"},open(sys.argv[1],"w"),indent=2)' "$OUT" "$rss"
cat "$OUT"
