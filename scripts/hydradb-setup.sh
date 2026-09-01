#!/usr/bin/env bash
# Start HydraDB — the shared lab graph database.
#
# Usage:
#   ./scripts/hydradb-setup.sh          # start HydraDB
#   ./scripts/hydradb-setup.sh status   # check if running
#   ./scripts/hydradb-setup.sh stop     # stop container
#
# Any VPS can connect:
#   export HYDRADB_BOLT="bolt://<this-vps-ip>:7687"
#   export HYDRADB_TOKEN="private-lab-hydradb-token-2026-secure"
set -euo pipefail

CONTAINER="hydradb"
IMAGE="ghcr.io/hydra-db/hydradb:latest"
DATA_DIR="/root/hydradb-data"
TOKEN="private-lab-hydradb-token-2026-secure"
TOKEN_FILE="$DATA_DIR/auth-token"

# Ports (bound to localhost for security — use SSH tunnel for remote access)
BOLT_PORT=7687
HTTP_PORT=8443
ADMIN_PORT=9090

mkdir -p "$DATA_DIR/store" "$DATA_DIR/cache"
echo "$TOKEN" > "$TOKEN_FILE"

cmd_start() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "HydraDB already running."
        docker ps --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        return 0
    fi

    # Remove stale container if it exists but is stopped
    docker rm "$CONTAINER" 2>/dev/null || true

    echo "Starting HydraDB..."
    docker run -d \
        --name "$CONTAINER" \
        --restart unless-stopped \
        -v "$DATA_DIR:/data" \
        -p 127.0.0.1:${BOLT_PORT}:7687 \
        -p 127.0.0.1:${HTTP_PORT}:8443 \
        -p 127.0.0.1:${ADMIN_PORT}:9090 \
        -e GRAPH_NAMESPACE=default \
        -e GRAPH_ID=lab \
        -e GRAPH_CELL_ID=cell-0 \
        -e CLOUD_PROVIDER=local \
        -e LOCAL_PATH=/data/store \
        -e GRAPH_DATA_PATH=data \
        -e GRAPH_CELLS=cell-0 \
        -e GRAPH_NODE_ID=node-0 \
        -e GRAPH_ALLOW_PLAINTEXT=true \
        -e GRAPH_AUTH_TOKEN_FILE=/data/auth-token \
        -e GRAPH_BOLT_NODE_ADDRESSES=node-0=127.0.0.1:7687 \
        -e GRAPH_ADVERTISED_BOLT_ADDR=127.0.0.1:7687 \
        -e GRAPH_DATA_CACHE_DIR=/data/cache \
        -e RUST_LOG=info \
        -e RUST_MIN_STACK=33554432 \
        "$IMAGE"

    # Wait for ready
    echo "Waiting for HydraDB to be ready..."
    for i in $(seq 1 30); do
        if curl -sf http://127.0.0.1:${ADMIN_PORT}/metrics 2>/dev/null | grep -q "graph_runtime_ready 1"; then
            echo "HydraDB is ready."
            echo ""
            echo "  Bolt:    bolt://127.0.0.1:${BOLT_PORT}"
            echo "  HTTP:    http://127.0.0.1:${HTTP_PORT}"
            echo "  Admin:   http://127.0.0.1:${ADMIN_PORT}"
            echo "  Token:   $TOKEN"
            echo ""
            echo "Remote VPS access via SSH tunnel:"
            echo "  ssh -L ${BOLT_PORT}:localhost:${BOLT_PORT} user@$(hostname -I | awk '{print $1}')"
            return 0
        fi
        sleep 1
    done

    echo "HydraDB failed to start. Check: docker logs $CONTAINER"
    return 1
}

cmd_status() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "HydraDB is running."
        docker ps --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        curl -sf http://127.0.0.1:${ADMIN_PORT}/metrics 2>/dev/null | grep "graph_runtime_ready" || echo "  (metrics not available yet)"
    else
        echo "HydraDB is not running."
    fi
}

cmd_stop() {
    docker stop "$CONTAINER" 2>/dev/null && echo "HydraDB stopped." || echo "HydraDB was not running."
}

case "${1:-start}" in
    start)  cmd_start ;;
    status) cmd_status ;;
    stop)   cmd_stop ;;
    *)      echo "Usage: $0 {start|status|stop}" ;;
esac
