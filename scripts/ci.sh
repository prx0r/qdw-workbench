#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
python3 tests/validate_structure.py
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
npm ci --prefix apps/desktop/web
npm run typecheck --prefix apps/desktop/web
npm test --prefix apps/desktop/web
npm run build --prefix apps/desktop/web
python3 tests/mutation_harness.py
