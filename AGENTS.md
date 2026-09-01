# AGENTS.md — Private Lab

The local control plane for Moltwork. Desktop app, native graph database, agent vault, human queue.

## What is Private Lab?

A Tauri 2 desktop app that is the **private controller** for your Moltwork operation. The browser (oracle.moltwork.com) is the lightweight public oracle — opportunities, data, stats. The desktop is where real work happens.

### Core capabilities

- **Vault**: All private keys, mnemonics, API secrets (never exposed to browser)
- **HydraDB**: Native Rust graph database — the canonical experience graph
- **CGE**: Run experiments locally (adversarial world evolution)
- **Letta**: Persistent agent memory and skills
- **Git**: Worker version lineage (content-addressed)
- **Budget**: Real spending decisions (BATS routing)
- **Oracle**: Connect to opportunity feeds
- **Human Queue**: Approve/decline agent actions with comments
- **Agent Avatars**: three.ws integration — see agents on jobs, review progress

## HydraDB — The Native Graph Database

**HydraDB is a Rust distributed graph database, NOT SQLite.**

- Object-store native (S3-compatible)
- OpenCypher queries over Bolt 5.x or HTTPS
- GraphBLAS-accelerated traversal
- Snapshot-consistent reads
- Durable on SlateDB + object storage
- **Any client connects to the same lab** — desktop or VPS

### Connection

```bash
# Docker status
docker ps | grep hydradb

# Auth token
echo "private-lab-hydradb-token-2026-secure"

# Bolt: bolt://127.0.0.1:7687
# HTTP: http://127.0.0.1:8443
# Admin: http://127.0.0.1:9090

# Python
from integrations.hydra import get_client
client = get_client()  # connects to localhost:7687

# Remote VPS
export HYDRADB_BOLT="bolt://vps-ip:7687"
export HYDRADB_TOKEN="private-lab-hydradb-token-2026-secure"
```

The SQLite files in workerkit/mwgym (`lab_projection.db`, `graph_store.db`, `unified_lab.db`) are **disposable projections** — local caches that can be rebuilt from the event ledger. They are NOT HydraDB.

When HydraDB is running, all graph queries go through Bolt/HTTP. The SQLite projections exist only as a fallback during development.

### HydraDB data model

Two orthogonal axes:
- **CapabilityPool**: what domain (security, forecasting, coding)
- **Venue**: where you compete (bittensor/sn60, immunefi, metaculus)

A run belongs to ONE venue and ONE or MORE capability pools.

```
Nodes: Worker, WorkerVersion, Run, Studio, TaskInstance, Experiment,
       LearningProposal, Finding, Artifact, BudgetEvent, CapabilityPool, Venue

Edges: HAS_VERSION, RAN, IN_STUDIO, ATTEMPTED, PART_OF, SUPPORTED_BY,
       CREATED, VALID_IN, TRANSFERRED_TO, COST, RECEIVED, PRODUCED,
       MEMBER_OF (Worker→Pool), CONTRIBUTES_TO (Run→Pool),
       EXECUTED_AT (Run→Venue), APPLIES_TO (Finding→Pool),
       HAS_VENUE (Pool→Venue)
```

### HydraDB client (Python)

```python
from integrations.hydra import (
    get_client, create_worker, create_run, create_experiment,
    lab_summary, finding_to_studio, studio_stats,
)

# Connect (singleton, reuses connection)
client = get_client()

# Write: create subgraphs (only pattern HydraDB supports)
create_worker(worker_id="r1", name="Research Agent",
              version_id="v1", model="mimo-v2.5")

create_run(run_id="run-001", studio_id="metaculus",
           outcome="won", task_family="forecasting")

create_experiment(experiment_id="exp-001", studio_id="metaculus",
                  hypothesis="base-rate improves calibration")

# Read: MATCH traversals
lab_summary()
finding_to_studio()
studio_stats("metaculus")
```

### HydraDB Cypher constraints

```python
# ✅ WORKS
session.run('CREATE (a {id: 1})-[:FOLLOWS]->(b {id: 2})')  # CREATE with edge
session.run('MATCH (n:Worker) RETURN n.id AS id')            # property return
session.run('MATCH (n:Worker) RETURN count(*) AS count')     # count(*)
session.run('MATCH (n:Worker {id: $id}) DETACH DELETE n')   # delete

# ❌ BROKEN
session.run('CREATE (n:Worker {id: "x"})')    # standalone CREATE
session.run('MERGE (n:Worker {id: 1})')        # MERGE
session.run('MATCH (a) CREATE (a)-[:EDGE]->(b)')  # MATCH+CREATE
session.run('MATCH (n) RETURN n')              # whole node return
session.run('MATCH (n) RETURN count(n)')       # count(n)
```

## Capability Pools

The lab has two orthogonal axes:

| Axis | Examples |
|------|----------|
| **CapabilityPool** | security, forecasting, coding, research |
| **Venue** | bittensor/sn60, immunefi, metaculus |

A run belongs to ONE venue and ONE or MORE capability pools.

### Pool architecture

```
ORACLE tags opportunity → pool
     ↓
CAPABILITY POOL handles it (shared doctrine + evidence + skills)
     ↓
executes through venue adapter (bittensor, immunefi, etc.)
     ↓
HYDRADB records what happened
     ↓
pool workers gain retrieval access
     ↓
CGE tests promising lessons
     ↓
GIT promotes validated skill
     ↓
next venue worker inherits it
```

### Pool-based queries

```python
from integrations.hydra import (
    create_pool, create_pool_venue, create_worker_in_pool,
    get_pool_stats, get_pool_findings, get_transferred_findings,
)

# Create pool with venues
create_pool(pool_id='security', name='security')
create_pool_venue(pool_id='security', venue_id='bitsec', venue_name='Bitsec SN60')

# Query pool
get_pool_stats('security')        # runs, findings, workers, venues
get_pool_findings('security')     # all findings in pool
get_transferred_findings()        # findings that crossed venues
```

## The Three Layers

### 1. Public Web (oracle.moltwork.com)
- Read-only opportunity data
- Subnet rankings, leaderboards
- Agent stats (sign in to track your agents)
- No auth, no private keys
- Static site on Cloudflare Pages

### 2. Authenticated Web (app.moltwork.com)
- Track YOUR wallets, YOUR submissions
- Portfolio view, P&L
- Still no keys on server
- Sign transactions locally, broadcast

### 3. Local Desktop (private-lab) — THIS IS THE CONTROLLER
- Holds all secrets (Vault)
- Makes all decisions
- HydraDB runs here (native graph)
- Broadcasts to chain
- Never exposes keys to browser
- Agent avatars via three.ws
- Human queue for approvals

## Studios

 Studios are domain adapters plugged into the global Lab. The Lab supplies the scientific method. Studios supply domains.

```
PRIVATE LAB
    │
    ├── HydraDB (Rust, native graph)
    ├── Vault (keys, mnemonics, secrets)
    ├── CGE (experiments, worlds, adversary)
    ├── Letta (persistent agent memory)
    ├── Git (worker versions, content-addressed)
    ├── Budget (BATS routing, spending)
    ├── Human Queue (approvals)
    ├── three.ws (agent avatars, job status)
    │
    ├── Studio: Metaculus (forecasting)
    ├── Studio: Bittensor (distributed inference)
    ├── Studio: Security (vulnerability research)
    ├── Studio: Hackathon Hub
    └── future Studios
```

### Metaculus Studio
- Submit forecasts via API
- Track tournament performance
- Historical replay training
- Brier score optimization

### Bittensor Studio
- Monitor subnet emissions
- Manage miner registrations
- Track earnings per subnet
- Optimize compute allocation

## Browser vs Desktop

| | Browser (oracle.moltwork.com) | Desktop (private-lab) |
|---|---|---|
| **Role** | Public oracle, data viewer | Private controller |
| **Auth** | Optional sign-in | Always local |
| **Keys** | Never | Vault (never exposed) |
| **Data** | Opportunities, leaderboards | Everything: experiments, runs, graphs |
| **Actions** | Read-only | Submit, approve, execute |
| **HydraDB** | No | Yes (native) |
| **Agent status** | View only | Full control |

## API Surface

### qdw-node (localhost:9902)

| Endpoint | What |
|----------|------|
| `/v1/health` | Node status |
| `/v1/metrics` | CPU, RAM, disk |
| `/v1/git/*` | Worktree management |
| `/v1/process` | Spawn processes |
| `/v1/sessions` | Agent sessions |
| `/v1/context/compile` | Context assembly |
| `/v1/handovers` | Session handovers |

### Private Lab Bridge (localhost:9911)

| Endpoint | What |
|----------|------|
| `/v1/products` | Product registry |
| `/v1/human/pending` | Human approvals |
| `/v1/memory/*` | Cross-session memory |
| `/v1/metaculus/*` | Metaculus operations |
| `/v1/bittensor/*` | Bittensor operations |

## Key Invariants

1. **Private Lab is the controller.** Web dashboard is a viewer.
2. **Never expose keys to browser.** Sign locally, broadcast.
3. **HydraDB is the native graph database.** SQLite projections are disposable caches.
4. **Handovers are SHA-256 bound.** No forgery.
5. **Budget decisions are local.** BATS routes, not cloud.
6. **Studios are domain adapters.** The Lab is the scientific method.

## Connecting to Remote Nodes

```bash
# Install node on VPS
./scripts/install-node.sh user@vps

# SSH tunnel from desktop
ssh -L 9902:localhost:9902 user@vps

# Now localhost:9902 talks to VPS
curl http://localhost:9902/v1/metrics
```

## Multi-Device Sync

- **Git**: Worker versions sync via remote
- **Handovers**: Context transfers between nodes
- **Oracle**: Shared opportunity data
- **HydraDB**: Per-node graph (sync via Git or replication)
