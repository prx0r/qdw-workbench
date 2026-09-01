#!/usr/bin/env python3
"""Quick test: is HydraDB live and accessible?

Usage:
    python3 scripts/hydradb-test.py                  # test localhost
    python3 scripts/hydradb-test.py bolt://vps:7687  # test remote
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.hydra.client import HydraClient, hash_id

bolt = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HYDRADB_BOLT", "bolt://127.0.0.1:7687")
token = os.environ.get("HYDRADB_TOKEN", "private-lab-hydradb-token-2026-secure")

print(f"Testing HydraDB at {bolt}...")

try:
    client = HydraClient(bolt_url=bolt, auth_token=token)
    client.connect()
    health = client.health()
    print(f"  Status: {health['status']}")
    print(f"  Workers in graph: {health.get('workers', 0)}")

    # Quick write+read test
    client.run_write(
        'CREATE (t:TestProbe {id: $id, ts: $ts})-[:_PROBE]->(t2:TestProbe {id: $id2})',
        id=hash_id("probe"), ts=str(int(__import__("time").time())),
        id2=hash_id("probe2")
    )
    count = client.count_nodes("TestProbe")
    client.clear_label("TestProbe")
    print(f"  Write/read: OK ({count} probe nodes created)")
    print(f"\nHydraDB is LIVE and working.")
    client.close()
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)
