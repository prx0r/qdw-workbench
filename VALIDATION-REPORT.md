# Validation report

Generated 2026-08-19.

Executed successfully in the generation environment:

- `python3 tests/validate_structure.py` — PASS
- `python3 tests/mutation_harness.py` — PASS; killed public-bind and detached-QDW-authority mutations
- `python3 -m compileall integrations/qdw_bridge/src` — PASS
- ZIP CRC/integrity test — PASS

Not executable in the generation environment because Rust is not installed and outbound package registries are unavailable:

- `cargo fmt/clippy/test --workspace`
- Tauri Linux build
- npm dependency install / Vitest / Vite production build
- live Hermes ACP launch
- live QDW bridge against cloned repo

These are mandatory CI gates in `.github/workflows/ci.yml` and `scripts/ci.sh`; absence of local execution here MUST NOT be represented as PASS. The first implementation agent should run them before merging or claiming a usable release.
