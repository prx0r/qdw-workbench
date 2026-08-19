#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
mkdir -p build
python3 tests/validate_structure.py
python3 -c 'from pathlib import Path; import hashlib,json,time; root=Path("."); fs=[{"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size} for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts and "target" not in p.parts]; Path("build/SOURCE-MANIFEST.json").write_text(json.dumps({"created_unix":time.time(),"files":fs},indent=2))'
