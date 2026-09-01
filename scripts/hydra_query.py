#!/usr/bin/env python3
"""HydraDB query helper — called by Tauri (Rust) as subprocess.

Usage:
    echo '{"query":"MATCH (n:Worker) RETURN n.name AS name"}' | python3 scripts/hydra_query.py
    python3 scripts/hydra_query.py --summary
    python3 scripts/hydra_query.py --health
    python3 scripts/hydra_query.py --pools
    python3 scripts/hydra_query.py --pool-stats security
    python3 scripts/hydra_query.py --pool-findings security
    python3 scripts/hydra_query.py --transferred
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.hydra.client import HydraClient

def main():
    client = HydraClient()
    client.connect()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--health":
            print(json.dumps(client.health()))
        elif arg == "--summary":
            from integrations.hydra.query import lab_summary
            print(json.dumps(lab_summary()))
        elif arg == "--count":
            label = sys.argv[2] if len(sys.argv) > 2 else "Worker"
            print(json.dumps({"label": label, "count": client.count_nodes(label)}))
        elif arg == "--list":
            label = sys.argv[2] if len(sys.argv) > 2 else "Worker"
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            results = client.list_nodes(label, limit)
            print(json.dumps(results))
        elif arg == "--pools":
            from integrations.hydra.query import pool_summary
            print(json.dumps(pool_summary()))
        elif arg == "--pool-stats":
            pool_name = sys.argv[2] if len(sys.argv) > 2 else "security"
            from integrations.hydra.query import get_pool_stats
            print(json.dumps(get_pool_stats(pool_name)))
        elif arg == "--pool-findings":
            pool_name = sys.argv[2] if len(sys.argv) > 2 else "security"
            from integrations.hydra.query import get_pool_findings
            print(json.dumps(get_pool_findings(pool_name)))
        elif arg == "--transferred":
            from integrations.hydra.query import get_transferred_findings
            print(json.dumps(get_transferred_findings()))
        else:
            print(json.dumps({"error": f"unknown arg: {arg}"}))
    else:
        # Read query from stdin
        try:
            data = json.load(sys.stdin)
            query = data.get("query", "")
            params = data.get("params", {})
            if not query:
                print(json.dumps({"error": "no query provided"}))
                sys.exit(1)
            results = client.run(query, **params)
            print(json.dumps(results))
        except json.JSONDecodeError:
            print(json.dumps({"error": "invalid JSON input"}))
            sys.exit(1)

    client.close()

if __name__ == "__main__":
    main()
