from pathlib import Path
R=Path(__file__).resolve().parents[1]
required=["Cargo.toml","crates/contracts/src/lib.rs","crates/qdw-node/src/main.rs","crates/acp-host/src/lib.rs","apps/desktop/src-tauri/tauri.conf.json","apps/desktop/web/src/App.tsx","integrations/qdw_bridge/src/qdw_workbench_bridge/app.py","docs/TESTING_AND_ANTI_CHEAT.md"]
missing=[x for x in required if not (R/x).exists()]
if missing: raise SystemExit(f"missing required files: {missing}")
b=(R/'integrations/qdw_bridge/src/qdw_workbench_bridge/app.py').read_text()
assert 'from qdw.system import QDWSystem' in b
for forbidden in ['CREATE TABLE products','CREATE TABLE human_actions','CREATE TABLE factory_runs','BuildCertificate(']:
    assert forbidden not in b, f"bridge duplicates authority: {forbidden}"
t=(R/'apps/desktop/src-tauri/capabilities/default.json').read_text(); assert 'shell:allow-execute' not in t
n=(R/'crates/qdw-node/src/config.rs').read_text(); assert '127.0.0.1:9902' in n
anti=(R/'docs/TESTING_AND_ANTI_CHEAT.md').read_text(); assert 'deliberately broken' in anti and 'client-provided `passed=true`' in (R/'README.md').read_text()
print(f"STRUCTURE PASS: {len(required)} required paths, authority boundaries present")
