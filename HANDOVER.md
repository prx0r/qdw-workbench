# HANDOVER — QDW Workbench Build Session
**Date:** 2026-08-19
**Workspace:** `/home/box/qdw-workbench/`
**Previous agent:** opencode (mimo-v2.5)

## What was accomplished

### Binaries built
- `qdw-node` — 6.6MB, all 12 original API endpoints + 8 new session/PTY endpoints
- `qdw-workbench-desktop` — 19.5MB Tauri 2 app (first build complete, rebuild in progress)

### Vendor repos cloned (12 total)
- `qdw` — canonical QDW source
- `qdw-forge` — factory/verification
- `gitgoblin` — frontier discovery
- `hermes-lcm` — Lossless Context Management plugin (installed)
- `hermes-memory-installer` — 3-tier memory (deps installed)
- `superpowers` — 14 coding skills (installed)
- `code-review-graph` — v2.3.7 MCP server (installed)
- `ego-lite` — browser automation (macOS only)
- `hermes-browser-extension` — Chrome side panel
- `hermes-control-interface` — web dashboard (built)
- `awesome-hermes-agent` — ecosystem directory
- `memory-os` — 7-layer memory system (core deps installed)

### Integration wiring
- hermes-lcm plugin registered with Hermes
- 14 superpowers skills installed (TDD, debugging, review, brainstorming, etc.)
- code-review-graph configured as MCP server
- memory bridge created (`memory_bridge.py` — SQLite store/search/recall)
- LCM provider created (`lcm_provider.py` — assertions → ContextFragments)
- Hermes config updated with code-review-graph and qdw-bridge MCP servers

### New code written
- `crates/qdw-node/src/session.rs` — SessionStore for persistent agent sessions
- `crates/qdw-node/src/pty.rs` — PTY registry using portable-pty
- `crates/qdw-node/src/app.rs` — 8 new endpoints (sessions + PTY)
- `crates/acp-host/src/lib.rs` — fixed to use correct ACP SDK API
- `integrations/qdw_bridge/src/qdw_workbench_bridge/memory_bridge.py` — memory storage
- `integrations/qdw_bridge/src/qdw_workbench_bridge/lcm_provider.py` — LCM → context
- `apps/desktop/web/src/components/AgentPanel.tsx` — multi-turn session UI
- `apps/desktop/web/src/components/TerminalPanel.tsx` — PTY-based terminal
- `apps/desktop/web/src/components/MemoryPanel.tsx` — memory search/display
- `apps/desktop/src-tauri/src/commands.rs` — 8 new Tauri commands
- `scripts/qdw-launch` — master launcher
- `scripts/qdw-stop` — stop all processes
- `~/.local/share/applications/qdw.desktop` — desktop launcher

### What was tested and works
- qdw-node: all 12 original endpoints (health, metrics, git, process, context, handover)
- qdw-node: session create/list/prompt/close (new)
- QDW bridge: all 15 endpoints against live QDW database
- Memory: store/recent/search (SQLite-backed)
- LCM: assertions → context fragments
- Handover: SHA-256 verified, persisted to disk, append-only
- Context compiler: trust ordering, budget enforcement, digest
- TypeScript: compiles clean
- Frontend: builds 481KB bundle
- Hermes: ACP check passes, 90 skills, hermes-lcm plugin
- Desktop launcher: .desktop file created

## Build status

### qdw-node — DONE
Built at `/root/mangy-cargo-target/release/qdw-node`

### Tauri desktop — IN PROGRESS
First build complete at `/root/mangy-cargo-target/release/qdw-workbench-desktop` (19.5MB).
Rebuild with new code (sessions, PTY, memory) is running.
Check: `tail -5 /tmp/opencode/qdw_final_build.log`

To restart the build if it failed:
```bash
cd /home/box/qdw-workbench
CARGO_TARGET_DIR=/root/mangy-cargo-target cargo build --release -j1
```

## What's NOT done (remaining dev steps)

### P0 — Must do
1. **Complete Tauri binary rebuild** — new code written but binary not yet produced
2. **Fix ACP one-shot response** — currently returns stop_reason, not actual text. Need to handle `SessionNotification` with `AgentMessageChunk` to collect streamed text
3. **PTY resize** — `resize()` in pty.rs is a no-op. Need to store master fd and call `pair.master.resize()`
4. **Run `cargo test --workspace`** — verify all tests pass
5. **Run `cargo fmt --check`** — format all Rust code

### P1 — Should do
6. **Wire ContextMeter to ACP context usage** — read context tokens from session responses
7. **CostPanel** — currently shows "---". Wire to QDW ledger for real cost data
8. **Verification display** — show QDW verification status in ProductsPanel
9. **SSH tunnel lifecycle** — add stop/reconnect/monitoring (currently start-only)
10. **Federation panel** — show real data from `/v1/federation/health`

### P2 — Nice to have
11. **Persistent ACP streaming** — use `start_session()` + `read_update()` for real streaming
12. **OpenTelemetry exporter** — OTLP export of run events
13. **LSP/SCIP** — code intelligence
14. **Telegram HumanQueue notifications**
15. **Context A/B experiment page**

## How to launch

```bash
# Full stack
~/qdw-workbench/scripts/qdw-launch

# Or manually
~/mangy-cargo-target/release/qdw-node --config ~/.config/qdw-node/config.toml &
PYTHONPATH=~/qdw-workbench/vendor/qdw/src QDW_DB=~/.local/share/qdw-workbench/test-qdw.db \
  ~/qdw-workbench/.venv/bin/python3 -m qdw_workbench_bridge.cli &
~/mangy-cargo-target/release/qdw-workbench-desktop
```

Find "QDW" in the application menu.

## Key files for continuation

| File | What |
|------|------|
| `/home/box/qdw-workbench/AGENTS.md` | Agent reference for API, endpoints, how-to |
| `/home/box/qdw-workbench/docs/AGENT_IMPLEMENTATION_HANDOFF.md` | Original P0/P1 task list |
| `/home/box/qdw-workbench/crates/acp-host/src/lib.rs` | ACP integration (needs text streaming fix) |
| `/home/box/qdw-workbench/crates/qdw-node/src/pty.rs` | PTY terminal (needs resize fix) |
| `/home/box/qdw-workbench/crates/qdw-node/src/session.rs` | Session management |
| `/home/box/qdw-workbench/crates/qdw-node/src/app.rs` | All API routes |
| `/home/box/qdw-workbench/apps/desktop/web/src/components/AgentPanel.tsx` | Multi-turn agent UI |
| `/home/box/qdw-workbench/apps/desktop/web/src/components/TerminalPanel.tsx` | PTY terminal UI |
| `/home/box/qdw-workbench/integrations/qdw_bridge/src/qdw_workbench_bridge/app.py` | Bridge endpoints |
| `/home/box/qdw-workbench/integrations/qdw_bridge/src/qdw_workbench_bridge/memory_bridge.py` | Memory storage |
| `/home/box/qdw-workbench/scripts/qdw-launch` | Master launcher |

## QDW integration status

The bridge correctly imports `from qdw.system import QDWSystem` from `vendor/qdw/src`.
Federation health returns 4 systems (gitgoblin, dell, forge, sandbox) — all "not configured".
Products, factories, human queue are empty (no data in test DB).

To populate with real QDW data, set `QDW_DB` to a path with actual QDW tables.
