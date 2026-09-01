# PRIVATE LAB — Build Plan

## Vision

One control lab (private-lab). Separate repos are modules that plug in.
Build the center first. Integrate later once patterns are canonical.

## Current State

| Component | Status | What exists |
|-----------|--------|-------------|
| HydraDB | LIVE | Docker container, Python client, schema, queries |
| Contracts | DONE | Pydantic models for all lab entities (337 lines) |
| Tauri app | SCAFFOLD | Rust crate exists, panels exist, not wired |
| qdw-node | FUNCTIONAL | API endpoints work, no HydraDB endpoint |
| Studios | STUBS | Metaculus + Bittensor adapter skeletons |
| workerkit | MODULE | Execution kernel, needs HydraDB wiring |
| mwgym | MODULE | Training layer, needs HydraDB wiring |
| oracle | MODULE | Market intelligence, works standalone |
| CG | MODULE | Evolution kernel, works standalone |

## Phase 1: Make private-lab the control plane (this week)

### 1.1 Wire qdw-node to HydraDB
- Add `/v1/hydra` endpoint to `crates/qdw-node/src/app.rs`
- Endpoint accepts Cypher queries, returns results as JSON
- Shells out to Python client or uses HTTP API for reads

### 1.2 Wire Tauri commands to HydraDB
- Add `hydra_query` command to `apps/desktop/src-tauri/src/commands.rs`
- Frontend can call `invoke("hydra_query", {query: "..."})` 

### 1.3 Build HydraDB panel in Tauri frontend
- `apps/desktop/web/src/components/HydraPanel.tsx`
- Shows: lab summary (workers, runs, experiments, findings)
- Shows: graph visualization (nodes + edges)
- Allows: manual Cypher queries

### 1.4 Add tests for HydraDB integration
- `tests/test_hydra.py` — write, read, traverse, cleanup
- Verify multi-studio isolation
- Verify content-addressed run IDs

## Phase 2: Wire modules to HydraDB (next week)

### 2.1 workerkit — Wire HydraDB in orchestrator
- Replace `# TODO: Wire real HydraDB client` in `orchestrator.py`
- After each run, create Run + WorkerVersion subgraph in HydraDB
- `wk lab summary` reads from HydraDB instead of SQLite

### 2.2 mwgym — Wire HydraDB in wired_loop
- Replace `# TODO: Wire real HydraDB client` in `wired_loop.py`
- After each training round, record WorldGenome + Run in HydraDB
- Lab brief reads from HydraDB

### 2.3 oracle — Leave as-is
- Oracle finds opportunities, writes to its own SQLite
- Private-lab pulls opportunities via Oracle API
- No HydraDB needed for oracle

## Phase 3: Build Studios (week 3)

### 3.1 Metaculus Studio
- Wire `studios/metaculus/adapter.py` to Metaculus API
- Submit forecasts, track scores, record in HydraDB
- ForecastingWorld class in mwgym for CGE training

### 3.2 Bittensor Studio
- Wire `studios/bittensor/` to Bittensor subnet APIs
- Monitor emissions, manage miners, record in HydraDB

### 3.3 Human Queue
- Wire `HumanQueue.tsx` to qdw-node
- Approvals for: production WorkerVersion promotion, large spend, external submissions

## Phase 4: Dashboard + Gamification (week 4)

### 4.1 Dashboard panels
- CONTROL: active runs, experiments, pending promotions, spending
- WORKERS: lineage tree, version history, performance
- EXPERIMENTS: hypothesis, control vs candidate, results
- RUNS: immutable execution browser
- EVIDENCE: findings, transfer claims, doctrine
- BUDGET: quality/cost frontier, routing decisions
- GRAPH: HydraDB visualization

### 4.2 three.ws agent avatars
- Agent status display (on job, idle, learning)
- Progress tracking per agent

### 4.3 Gamification
- Leaderboard: best worker versions, win rates
- Achievements: first promotion, first transfer, first $ earned

## Principles

1. **private-lab is the center.** Everything plugs into it.
2. **Separate repos stay separate** while experimenting. Integrate once patterns are canonical.
3. **HydraDB is the shared brain.** Any VPS connects to the same graph.
4. **CG is the evolution engine.** It stays separate, plugs in via adapters.
5. **Build the minimum that works.** No premature optimization.
