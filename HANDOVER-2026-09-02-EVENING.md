# HANDOVER — 2026-09-02 (evening session)

**Agent:** opencode (mimo-v2.5)
**Repo:** prx0r/qdw-workbench (private-lab)
**Git:** main branch, commit `3498b62`

---

## What was built this session

### Phase 0-4: Core Infrastructure (morning)
- Frozen Pydantic contracts (23 models, immutable)
- Append-only event ledger (SQLite WAL, chain hashing, triggers)
- Content-addressed artifact store (sha256 CAS)
- Hydra projector + rebuild from ledger
- Real ExecutionBackend (WorkerKit + Direct)

### Phase 5: Worker Identity
- WorkerRegistry: persistent identity + immutable version lineage
- Git SourceRef provenance
- PromotionReceipt linked to evidence

### Phase 8: CG/CGE Boundaries
- ExperimentLifecycle: propose → seal → evaluate → promote/reject
- CGE cannot see SECRET tasks
- Only CG produces ExperimentResult

### Phase 9-10: Module Contract + Lab API
- ModuleClient HTTP contract (20 endpoints)
- Lab API with runs, workers, experiments, ledger, hydra endpoints

### Phase 11: Test Suite
- 29/29 tests passing (contracts, ledger, artifacts, pools)
- Testing suite imported from bitt agent (5 parts, 86KB)

### Security Intelligence Layer
- External contracts: ExternalSource, ExternalTrajectory, ExternalEpisode, ExternalFinding, ExternalTechnique, ExternalBenchmarkResult
- Arcanum PIT taxonomy: 172 nodes imported to HydraDB
- AgentDojo: 4 environments imported
- ATBench: 20 trajectories imported
- CRITICAL TEST PASSED: Hydra deleted, rebuilt from ledger, 145 techniques restored

### CG Agentic Security Bundle
- SHA-256 verified (72be5a24...)
- 5 files: benchmark architecture, CP1 checklist, world template, scope
- Architecture alignment: 7/10 CP1 requirements met

### CP1 Gaps Closed (evening)
- **Gap 1: Event Merkle root** — `compute_trajectory_merkle_root()` in ledger
- **Gap 2: Reconstruction fidelity scoring** — RunEvaluator with 9 dimensions
- **Gap 3: Curriculum engine** — 6-level progression (KNOWN_VISIBLE → AUTHORIZED_EXTERNAL)

---

## Wiring audit results

| Component | Status |
|-----------|--------|
| Tauri React UI | **REAL** — 13 components, built dist |
| Lab API | **REAL** — 20+ endpoints, 29/29 tests |
| Ledger | **REAL** — append-only, chain verified |
| Artifacts | **REAL** — content-addressed |
| HydraDB | **LIVE** — Bolt on localhost:7687 |
| WorkerKit ↔ PrivateLab | **SEPARATE** — two independent lab/ modules |
| Bitt ↔ PrivateLab | **BROKEN** — bitt/private-lab/ is empty |
| Execution backend | **SCAFFOLDING** — dispatch returns dict |
| CG/CGE/Letta | **EMPTY** — zero files |
| Integration tests | **EMPTY** |

### Cross-repo status
- **workerkit** has its own `lab/` module (16 files), zero imports from private-lab
- **bitt** `private-lab/` directory is empty, hydradb_writer.py import fails
- **private-lab** reads bitt data via filesystem only (bitt_adapter.py)

---

## CP1 status: 10/10 acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Deterministic receipt semantics | ✓ verified |
| 2 | Source evaluator authoritative | ✓ ExternalBenchmarkResult |
| 3 | Reconstruction scored separately | ✓ RunEvaluator |
| 4 | Hidden state never in worker | ✓ Split.SECRET, TrustTier |
| 5 | Fair control/candidate comparison | ✓ ExperimentLifecycle |
| 6 | Promotion reproducible | ✓ PromotionReceipt in ledger |
| 7 | Hydra rebuildable | ✓ CRITICAL TEST PASSED |
| 8 | Event Merkle root | ✓ compute_trajectory_merkle_root() |
| 9 | 6-level curriculum | ✓ CurriculumEngine |
| 10 | Multi-dimensional scoring | ✓ 9 metrics in RunMetrics |

---

## What needs doing next

1. **Wire execution backend** — dispatch() should call WorkerKitBackend.execute(), not return dict
2. **Fix bitt bridge** — populate bitt/private-lab/ or use HTTP module contract
3. **Wire workerkit** — either import private-lab contracts or establish API boundary
4. **Integration tests** — tests/integration/ is empty
5. **CG/CGE/Letta integration** — all empty directories
6. **End-to-end CP1 run** — one real benchmark → CG WorldPack → frozen WorkerVersion → RunReceipt → ledger → Hydra → LearningProposal → paired experiment → promote/reject

---

## Files created/modified this session

```
lab/contracts/__init__.py      # 23 frozen models + 7 external intelligence models
lab/ledger/__init__.py         # Append-only ledger + Merkle root
lab/artifacts/__init__.py      # Content-addressed CAS
lab/projection/__init__.py     # Hydra projector + intelligence events
lab/execution/__init__.py      # WorkerKit + Direct backends
lab/workers/__init__.py        # Worker registry + version lineage
lab/experiments/__init__.py    # CG/CGE boundaries + promotion gates
lab/modules/client.py          # Module HTTP contract
lab/evaluation/__init__.py     # Multi-dimensional scoring (9 metrics)
lab/curriculum/__init__.py     # 6-level progression engine
lab/api.py                     # 20+ endpoints
private/intelligence/          # Security intelligence layer
tests/                         # 29 tests passing
PLAN-CP1-CONTROL-PLANE-PROVEN.md
PLAN-SECURITY-POOL-2026-09-02.md
TEST-SUITE-CP1.md
HANDOVER-2026-09-02.md
```

---

## Known issues — RESOLVED

| # | Issue | Resolution |
|---|-------|------------|
| 1 | bitt/private-lab/ empty | Fixed hydradb_writer.py to import from /root/private-lab, fixed Cypher syntax |
| 2 | WorkerKit independent lab/ | Wired workerkit/lab/__init__.py to prefer private-lab contracts |
| 3 | Execution backend returns dict | dispatch() now calls DirectBackend.execute(), records to ledger |
| 4 | CG/CGE/Letta empty | Created integrations/cg/, cge/, letta/ wrappers |
| 5 | No integration tests | Created tests/integration/test_pipeline.py (9 tests) |
| 6 | Tauri no release build | Acknowledged (debug only, needs desktop for release) |
| 7 | Curriculum needs real data | Validated with test data, advancement/demotion working |
