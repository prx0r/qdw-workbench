# QDW integration baseline

Inspected 2026-08-19.

- Repository: `prx0r/qdw`
- Baseline commit observed: `688a36ef2a945f7f4d564724f274122b1d63c0be` (federation integration).
- `QDWSystem` is the composition root and exposes canonical DB/ledger, WorkGraph, verification/certificates, factories/cost/learning, World/intelligence, HumanQueue, ProductRegistry and FederationService.
- Current public FastAPI is intentionally small: health, graph, factories, route. Workbench therefore adds a thin import-based bridge for UI projections; it does not duplicate QDW state.
- `FederationService.health()` currently projects GitGoblin, Dell, Forge and Sandbox configuration status.
- Human approvals must call canonical `HumanQueue`; its state machine and payload-hash binding remain authoritative.

Before implementation, the coding agent MUST re-read current QDW HEAD and reconcile any drift from this baseline rather than forcing this package's assumptions onto newer code.
