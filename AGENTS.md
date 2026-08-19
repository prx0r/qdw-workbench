# AGENTS.md — QDW Workbench

This is the agent-facing reference for the QDW Workbench desktop IDE.
If you are an AI agent (Hermes, Codex, OpenCode, etc.), read this first.

## What is QDW Workbench?

A Tauri 2 desktop app that gives you a single window into the QDW estate:
- **Editor**: CodeMirror 6, workspace files, save/load via Tauri IPC
- **Terminal**: Run commands via qdw-node process API (non-interactive)
- **Agent Panel**: Send prompts to Hermes via ACP one-shot
- **Human Queue**: Approve/decline QDW actions with comments
- **Memory**: Cross-session recall, search, store
- **Context Meter**: Shows context usage with pressure thresholds
- **Nodes**: Live CPU/RAM/disk for local and remote machines
- **Products**: QDW product registry
- **Federation**: GitGoblin, Dell, Forge, Sandbox status

## Architecture

```
You (agent) → ACP → Hermes → Workbench
                        ↓
                   qdw-node (localhost:9902)
                        ↓
                   QDW Bridge (localhost:9911)
                        ↓
                   QDW System (canonical authority)
```

**QDW is always the authority.** The workbench is a projection surface.
You cannot release products, approve actions, or issue certificates from here.

## API Surface

### qdw-node (localhost:9902)

| Endpoint | Method | What |
|----------|--------|------|
| `/v1/health` | GET | Node status, version |
| `/v1/metrics` | GET | CPU, RAM, disk, load, boot_id |
| `/v1/git/state?workspace=` | GET | HEAD, branch, dirty, remote |
| `/v1/git/diff?workspace=&scope=` | GET | uncommitted/staged/head diff |
| `/v1/git/worktree` | POST | Create git worktree |
| `/v1/process` | POST | Spawn process `{cwd, argv, env}` |
| `/v1/process/{id}/wait` | POST | Wait for exit, get stdout/stderr |
| `/v1/process/{id}/kill` | POST | Kill process |
| `/v1/events` | POST | Store run event (OpenTelemetry-shaped) |
| `/v1/context/compile` | POST | Compile context fragments under policy |
| `/v1/handovers` | POST | Persist handover with SHA-256 verification |
| `/v1/handovers/{session}/latest` | GET | Retrieve latest handover |
| `/v1/sessions` | GET | List active sessions |
| `/v1/sessions` | POST | Create session `{workspace, agent_command}` |
| `/v1/sessions/{id}` | GET | Get session info |
| `/v1/sessions/{id}` | DELETE | Close session |
| `/v1/sessions/{id}/prompt` | POST | Send prompt, get response |
| `/v1/pty` | POST | Spawn PTY `{cwd, shell, cols, rows}` |
| `/v1/pty` | GET | List PTY sessions |
| `/v1/pty/{id}` | GET | Get PTY info |
| `/v1/pty/{id}` | DELETE | Close PTY |
| `/v1/pty/{id}/write` | POST | Write to PTY `{data}` |
| `/v1/pty/{id}/read` | GET | Read from PTY `{data, available}` |

### QDW Bridge (localhost:9911)

| Endpoint | Method | What |
|----------|--------|------|
| `/health` | GET | QDWSystem.doctor() |
| `/v1/products` | GET | List all products |
| `/v1/products/{id}` | GET | Product passport |
| `/v1/factories` | GET | List factories |
| `/v1/human/pending` | GET | Pending human actions |
| `/v1/human/{id}/approve` | POST | Approve with actor_id + decision |
| `/v1/human/{id}/decline` | POST | Decline with actor_id + decision |
| `/v1/federation/health` | GET | Federation system status |
| `/v1/workgraphs` | GET | Work graphs |
| `/v1/workgraphs/{id}` | GET | Single workgraph + nodes |
| `/v1/recent-ledger` | GET | Recent ledger events |
| `/v1/memory/recent` | GET | Recent memory entries |
| `/v1/memory/search?q=` | GET | Search memory |
| `/v1/memory/store` | POST | Store memory entry |
| `/v1/context/lcm` | POST | LCM assertions → context fragments |

## How to use the agent panel (multi-turn sessions)

The agent panel now supports persistent multi-turn coding sessions:

```bash
# Create a session
curl -X POST http://127.0.0.1:9902/v1/sessions \
  -H 'Content-Type: application/json' \
  -d '{"workspace":"/path/to/project","agent_command":"hermes"}'
# Returns: {"session_id":"...","workspace":"...","agent_command":"hermes",...}

# Send a prompt (multi-turn)
curl -X POST http://127.0.0.1:9902/v1/sessions/{session_id}/prompt \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Fix the bug in src/main.rs"}'
# Returns: {"session_id":"...","response":"...","prompt_count":1}

# Send another prompt (same session)
curl -X POST http://127.0.0.1:9902/v1/sessions/{session_id}/prompt \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Now add a test for it"}'

# List active sessions
curl http://127.0.0.1:9902/v1/sessions

# Close a session
curl -X DELETE http://127.0.0.1:9902/v1/sessions/{session_id}
```

Each prompt connects to Hermes via ACP, executes in the session's workspace, and returns the response. The session tracks prompt count and workspace context.

## How to use the context compiler

```bash
curl -X POST http://127.0.0.1:9902/v1/context/compile \
  -H 'Content-Type: application/json' \
  -d '{
    "fragments": [
      {"provider_id":"qdw","source_uri":"qdw:invariant","observed_at":"2026-08-19T00:00:00Z","sha256":"a","token_estimate":100,"priority":100,"trust":"canonical","title":"invariant","content":"QDW is authority"},
      {"provider_id":"memory","source_uri":"mem:1","observed_at":"2026-08-19T00:00:00Z","sha256":"b","token_estimate":100,"priority":50,"trust":"memory","title":"memory","content":"user prefers dark mode"}
    ],
    "policy": {"version":"1","max_tokens":1000,"reserve_tokens":200}
  }'
```

Trust ordering: canonical > verified > observed > memory > ephemeral.
Budget is enforced. Dropped fragments are returned, not hidden.

## How to persist a handover

The body MUST be SHA-256 bound. Compute digest first:

```python
import hashlib
body = "## Objective\n..."
digest = hashlib.sha256(body.encode()).hexdigest()
```

Then POST with the correct `body_sha256`.

## How to store memory

```bash
curl -X POST http://127.0.0.1:9911/v1/memory/store \
  -H 'Content-Type: application/json' \
  -d '{"kind":"decision","source":"agent","content":"Used axum for HTTP","metadata":{"file":"app.rs"}}'
```

Kinds: `handover`, `product`, `approval`, `manual`, `decision`, `observation`.

## Running the workbench

```bash
# Full stack
~/qdw-workbench/scripts/qdw-launch

# Or manually
~/mangy-cargo-target/release/qdw-node --config ~/.config/qdw-node/config.toml &
PYTHONPATH=~/qdw-workbench/vendor/qdw/src QDW_DB=~/.local/share/qdw-workbench/test-qdw.db \
  ~/qdw-workbench/.venv/bin/python3 -m qdw_workbench_bridge.cli &
~/mangy-cargo-target/release/qdw-workbench-desktop
```

## Stopping

```bash
~/qdw-workbench/scripts/qdw-stop
```

## Key invariants

1. QDW is the authority. Workbench is a projection.
2. Handover digests are SHA-256 bound. No forgery.
3. Subscription units are never silently converted to USD.
4. The bridge owns no authoritative database.
5. Node binds to 127.0.0.1 by default (not public).
6. No shell:allow-execute in Tauri capabilities.
7. Context pressure: 70% warn, 82% prepare handover, 92% handover required.
