# Implementation Handoff for Coding Agent

This ZIP is intended to be imported next to `prx0r/qdw`, not blindly copied over it.

## Required sequence

1. Clone current `prx0r/qdw`, `NousResearch/hermes-agent`, and this package.
2. Record exact HEAD OIDs before modifying anything.
3. Run `python tests/validate_structure.py` in this package.
4. Install Rust/Node/Tauri dependencies and run `scripts/ci.sh` unchanged.
5. Start `qdw-workbench-bridge` with `PYTHONPATH` pointing at QDW's `src`.
6. Start `qdw-node` on loopback.
7. Launch the Tauri app.
8. Prove `/health`, factories, products and HumanQueue against real QDW.
9. Prove ACP with `hermes acp --check`, then a live Workbench ACP session.
10. Add live PTY streaming only after the noninteractive process path is proven; do not weaken command safety just to make terminal demos work.

## Do not do these things

- Do not copy QDW tables into a Workbench-owned canonical database.
- Do not create a second Factory/Product/Human approval model.
- Do not replace QDW verification with Workbench telemetry.
- Do not invent a QDW agent protocol; use ACP.
- Do not expose qdw-node unauthenticated on a public interface.
- Do not bundle Chromium for ordinary editor use; browser automation is optional/on-demand.
- Do not put Hindsight/GBrain/LCM content into `canonical` context class.
- Do not auto-promote agent-authored handover statements into QDW doctrine.

## P0 implementation tasks

- Make `cargo test --workspace` green on current stable Rust.
- Confirm exact Tauri v2 permissions needed and keep capability allowlist narrow.
- Extend the included official-ACP one-shot path into persistent streamed sessions; keep stable wire v1 negotiation and do not hand-roll JSON-RPC framing.
- Add a proper PTY crate (`portable-pty` or equivalent) only behind the node process interface, with bounded scrollback.
- Wire ContextMeter to ACP context usage when runtime supplies it; otherwise mark usage `estimated`, never fake exactness.
- Add SSH tunnel lifecycle with ControlMaster disabled by default and strict host-key checking inherited from user's SSH config.
- Add `QDW bridge /v1/federation` once the concrete current federation public API is inspected.

## P1

- SCIP index management.
- LSP lifecycle/proxy.
- OpenTelemetry OTLP exporter.
- Telegram HumanQueue notifications via Hermes skill, with QDW idempotency keys.
- Dell/Gold Standard API factory visual conformance page.
- Context A/B experiment page.

## Definition of done for first dogfood

You should be able to open Workbench after reboot and:

- see QDW + all configured repos and exact HEADs;
- see local/VPS CPU and RAM;
- open a QDW file and terminal;
- start Hermes in that workspace without an orientation prompt;
- see current context usage and cash/subscription usage separately;
- receive a generated handover before ending a long session;
- approve a real QDW HumanQueue item with a comment;
- inspect the resulting ledger event;
- compare at least two agent/context configurations on one verified task.
