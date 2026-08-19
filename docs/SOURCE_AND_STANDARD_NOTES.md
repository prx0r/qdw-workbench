# Source / standards notes (checked 2026-08-19)

- Tauri 2: Rust core + HTML/CSS/JS in OS WebView; Linux uses WebKitGTK. Keep privileged logic in Rust core.
- ACP: current stable wire protocol is v1; official Rust SDK `agent-client-protocol` 2.0.0 (2026-07-23) retains stable v1 wire schema while changing SDK APIs. Negotiate `protocolVersion`.
- Hermes: current repo exposes ACP editor mode with file, terminal, web/browser, memory, todo, session search, skills, execute/delegate and permission requests; the host controls whether permission UI reaches the human.
- QDW: bridge based on current `QDWSystem`, HumanQueue, ProductRegistry and FactoryDefinition. Current upstream public API remains small, hence the bridge.
- OpenTelemetry: use semantic-convention-shaped fields for telemetry, but QDW receipts/certificates remain authority.
- LSP/SCIP: planned P1 code-intelligence boundaries; not faked as already implemented in this V0.1 package.

The implementation agent must pin exact dependency lockfiles after first successful online build and commit them. Do not claim reproducibility before the lockfiles and release toolchain are frozen.
