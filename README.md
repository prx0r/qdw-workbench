# QDW Workbench

A lightweight Tauri 2 control plane and coding workbench for QDW.

QDW Workbench is deliberately **not another agent framework** and not another QDW kernel. It is the human surface over canonical QDW state plus a replaceable workstation/VPS execution daemon (`qdw-node`). Hermes is the primary agent runtime through ACP; other ACP-compatible runtimes can be attached without changing Workbench semantics.

## Goals

- Open one desktop app and immediately know the state of the QDW estate.
- Switch between local and remote workspaces without rebuilding project context manually.
- See products, factories, work graphs, verification, human approvals, nodes, CPU/RAM, costs, agent runs and context usage in one place.
- Compile task-specific agent context from QDW doctrine + code + memory + current evidence instead of dumping entire repositories into a prompt.
- Preserve session handovers as timestamped, hashed artifacts when a context window approaches its limit or a user ends a session.
- Treat human approvals as canonical QDW HumanQueue transitions, never frontend-only state.
- Keep the laptop light: no Electron, no mandatory Docker, Redis, Postgres, ClickHouse or background Chromium.

## Architecture

```text
Tauri Workbench
  ├── QDW bridge -> canonical QDWSystem / ledger / HumanQueue / Products
  ├── qdw-node local
  ├── qdw-node remote through SSH tunnels
  └── ACP host
       ├── hermes acp
       ├── Codex/other ACP agents
       └── future runtimes

qdw-node
  ├── /v1/health
  ├── /v1/metrics
  ├── /v1/workspaces
  ├── /v1/git/*
  ├── /v1/process/*
  ├── /v1/context/*
  ├── /v1/handovers/*
  └── local SQLite event/usage spool
```

## Current QDW compatibility

The bridge is written against the current QDW public structure (August 19, 2026): `QDWSystem`, `system.db`, `system.factories`, `system.human`, product/factory tables, WorkGraph tables, and the current `/health`, `/graph/{id}`, `/factories`, `/route` API. It adds a *thin adapter surface*; it does not create competing product or approval state.

## Quick start (developer machine)

Prerequisites: Rust stable, Node 22+, npm, Python 3.11+, Tauri Linux prerequisites (WebKitGTK), git, openssh-client.

```bash
./scripts/bootstrap.sh
./scripts/dev.sh
```

In another terminal, point the QDW bridge at a QDW checkout:

```bash
export PYTHONPATH=/path/to/qdw/src:$PYTHONPATH
export QDW_DB=/path/to/qdw/data/qdw.db
. .venv/bin/activate
qdw-workbench-bridge --listen 127.0.0.1:9911
```

Then configure `~/.config/qdw-workbench/config.toml` from `config/config.example.toml`.

## VPS node

```bash
./scripts/install-node.sh user@vps.example
```

This copies the release `qdw-node` binary and a user-systemd unit. The default node bind address is loopback. Workbench reaches it over an SSH local port-forward; do not publish node ports to the internet.

## Non-negotiable invariants

1. QDW remains authoritative for products, factory lineage, verification, release and human approvals.
2. A Workbench approval calls QDW HumanQueue and is bound to the exact request payload hash.
3. qdw-node is disposable execution infrastructure. It cannot issue QDW verification certificates.
4. Agent memory is candidate context, not QDW truth.
5. A context pack is a versioned/hashable compilation result; it is never the database of record.
6. A handover records source session, timestamps, workspace/commit, context usage and content digest.
7. Cost telemetry never silently converts subscription quota or local compute into fake USD.
8. No success UI may be driven by a client-provided `passed=true`; verification state must come from QDW.
9. Tests must include deliberately broken variants so a checker that cannot fail is itself considered broken.

See `docs/ARCHITECTURE.md`, `docs/TESTING_AND_ANTI_CHEAT.md`, and `docs/AGENT_IMPLEMENTATION_HANDOFF.md`.
