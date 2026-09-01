#!/usr/bin/env python3
"""HydraDB query helper — called by qdw-node (Rust) as subprocess.

Usage:
    echo '{"query":"MATCH (n:Worker) RETURN n.name AS name"}' | python3 scripts/hydra_query.py
    python3 scripts/hydra_query.py --summary
    python3 scripts/hydra_query.py --health
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
