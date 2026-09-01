# PRIVATE LAB — Build Plan (Revised)

## Vision

One control lab. Separate repos are modules. Modules own their ecosystems. Pools bridge knowledge. Lab allocates.

## Architecture

```
                    PRIVATE LAB
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
     MarketOracle       /bitt         other modules
         │               │
 external jobs       internal oracle
         │               │
         └──────┬────────┘
                ▼
          POOL MATCHER
                │
           Capability Pools
                │
                ▼
          Lab intelligence
```

## Current State

| Component | Status | What exists |
|-----------|--------|-------------|
| HydraDB | LIVE | Docker container, Python client, schema, queries |
| Contracts | DONE | Pydantic models for all lab entities |
| Module contract | DONE | ModuleStatus, PoolMatch, AllocationDecision |
| Module registry | DONE | Discover/track/query modules |
| Pool matcher | DONE | Cosine similarity + hierarchical shrinkage |
| Context compiler | DONE | Assembles SecurityLabBrief from pools |
| Lab controller | DONE | Full loop: ingest→match→allocate→dispatch→outcome |
| Lab Scientist | DONE | Reads evidence, proposes experiments |
| Module status API | DONE | FastAPI: /v1/modules, /v1/match, /v1/context |
| Pool queries | DONE | Dashboard wiring (Tauri + Python helper) |
| Bitt adapter | DONE | Read-only, reads bitt status |
| Transfer detection | DONE | Find findings that cross venues |
| Experiment tracking | DONE | CGE experiments in HydraDB |
| Budget allocator | DONE | Thompson-like with Gini anti-concentration |
| Tests | DONE | Pool matching + context compilation |
| Tauri app | SCAFFOLD | Rust crate exists, panels exist |
| Security Lab | DONE | 3 schools, 14 markets, doctrine, skills |

## What's Wired

- ✅ HydraDB → pool queries → dashboard
- ✅ Oracle security feeds → pool matcher (via feed adapters)
- ✅ Bitt module status → module registry (read-only)
- ✅ Pool matching → context compilation → dispatch
- ✅ Experiment tracking → HydraDB
- ✅ Transfer detection → pool evidence
- ✅ Budget allocation → Gini anti-concentration

## What Needs Wiring

- Security end-to-end (another agent doing worker lifecycle)
- Wire Letta to context compiler (worker memory)
- Wire CGE to experiment tracking
- Wire Git to promoted capabilities
- Full dashboard with pool visualization
- Real bitt adapter (connect to bitt's APIs, not just files)

## Key Files

| File | What |
|------|------|
| `lab/modules/__init__.py` | Module contract (ModuleStatus, PoolMatch, etc.) |
| `lab/modules/registry.py` | Module registry |
| `lab/modules/bitt_adapter.py` | Read-only bitt adapter |
| `lab/pools/matcher.py` | Pool matching |
| `lab/pools/transfers.py` | Transfer detection |
| `lab/pools/experiments.py` | Experiment tracking |
| `lab/context/compiler.py` | Context compilation |
| `lab/controller/__init__.py` | Lab controller |
| `lab/scientist/__init__.py` | Lab Scientist |
| `lab/budget/__init__.py` | Budget allocator |
| `lab/api.py` | FastAPI endpoints |
| `integrations/hydra/` | HydraDB client |
| `tests/test_pools.py` | Pool + context tests |
| `docs/ARCHITECTURE.md` | Full architecture guide |
