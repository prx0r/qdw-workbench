"""Lab API — canonical control API for Private Lab.

Endpoints for:
    - runs (CRUD)
    - workers (identity + versions)
    - experiments (lifecycle)
    - ledger (verification)
    - hydra (projector rebuild)
"""
from __future__ import annotations
import json
from typing import Any
from fastapi import FastAPI, HTTPException
from lab.modules import ModuleStatus, ModuleProgram, CapabilityDemand
from lab.modules.registry import ModuleRegistry
from lab.controller import LabController
from lab.pools.matcher import match_demand_to_pools
from lab.context.compiler import compile_context
from pydantic import BaseModel


class ContextRequest(BaseModel):
    pool_ids: list[str]
    total_tokens: int = 8000

app = FastAPI(title="Private Lab API", version="1.0.0")
controller = LabController()
registry = ModuleRegistry()


@app.get("/v1/health")
def health():
    return {"status": "ok", "modules": len(registry.list_modules())}


# ─── Modules ──────────────────────────────────────────────────────────

@app.post("/v1/modules/status")
def report_module_status(status: ModuleStatus):
    """Module reports its status to Private Lab."""
    controller.ingest_module_status(status)
    return {"received": True, "module_id": status.module_id, "programs": len(status.programs)}


@app.get("/v1/modules")
def list_modules():
    """List all registered modules."""
    return registry.summary()


@app.get("/v1/modules/{module_id}")
def get_module(module_id: str):
    """Get a specific module's status."""
    status = registry.get_module(module_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
    return status.model_dump()


@app.get("/v1/programs")
def list_programs():
    """List all programs across all modules."""
    programs = []
    for mid, prog in registry.get_all_programs():
        programs.append({"module_id": mid, **prog.model_dump()})
    return programs


@app.get("/v1/programs/{program_id}")
def get_program(program_id: str):
    """Get a specific program."""
    for mid, prog in registry.get_all_programs():
        if prog.program_id == program_id:
            return {"module_id": mid, **prog.model_dump()}
    raise HTTPException(status_code=404, detail=f"Program {program_id} not found")


# ─── Runs ─────────────────────────────────────────────────────────────

@app.get("/v1/runs")
def list_runs():
    """List all runs from the ledger."""
    from lab.ledger import Ledger
    ledger = Ledger()
    events = ledger.get_events_by_type("run.created", limit=100)
    runs = []
    for e in events:
        payload = json.loads(e["payload_json"])
        runs.append(payload)
    return {"runs": runs}


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str):
    """Get a run's full history from the ledger."""
    from lab.ledger import Ledger
    ledger = Ledger()
    events = ledger.get_entity_history(run_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {"run_id": run_id, "events": [json.loads(e["payload_json"]) for e in events]}


# ─── Workers ──────────────────────────────────────────────────────────

@app.get("/v1/workers")
def list_workers():
    """List all workers from the ledger."""
    from lab.ledger import Ledger
    ledger = Ledger()
    events = ledger.get_events_by_type("worker.created", limit=100)
    workers = []
    for e in events:
        payload = json.loads(e["payload_json"])
        workers.append(payload)
    return {"workers": workers}


@app.get("/v1/workers/{worker_id}")
def get_worker(worker_id: str):
    """Get a worker's version history."""
    from lab.ledger import Ledger
    from lab.artifacts import ArtifactStore
    from lab.workers import WorkerRegistry
    ledger = Ledger()
    artifacts = ArtifactStore()
    registry = WorkerRegistry(ledger, artifacts)
    history = registry.get_worker_history(worker_id)
    latest = registry.get_latest_version(worker_id)
    return {
        "worker_id": worker_id,
        "versions": history,
        "latest": latest,
    }


@app.get("/v1/workers/{worker_id}/versions")
def list_worker_versions(worker_id: str):
    """List all versions for a worker."""
    from lab.ledger import Ledger
    from lab.artifacts import ArtifactStore
    from lab.workers import WorkerRegistry
    ledger = Ledger()
    artifacts = ArtifactStore()
    registry = WorkerRegistry(ledger, artifacts)
    return {"worker_id": worker_id, "versions": registry.get_worker_history(worker_id)}


# ─── Experiments ──────────────────────────────────────────────────────

@app.get("/v1/experiments")
def list_experiments():
    """List all experiments from the ledger."""
    from lab.ledger import Ledger
    ledger = Ledger()
    events = ledger.get_events_by_type("experiment.created", limit=100)
    experiments = []
    for e in events:
        payload = json.loads(e["payload_json"])
        experiments.append(payload)
    return {"experiments": experiments}


@app.get("/v1/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    """Get an experiment's full history."""
    from lab.ledger import Ledger
    ledger = Ledger()
    events = ledger.get_entity_history(experiment_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    return {
        "experiment_id": experiment_id,
        "events": [json.loads(e["payload_json"]) for e in events],
    }


# ─── Ledger ───────────────────────────────────────────────────────────

@app.get("/v1/ledger/verify")
def verify_ledger():
    """Verify the entire ledger chain integrity."""
    from lab.ledger import Ledger
    ledger = Ledger()
    return ledger.verify_chain()


@app.get("/v1/ledger/summary")
def ledger_summary():
    """Get ledger summary."""
    from lab.ledger import Ledger
    ledger = Ledger()
    return ledger.summary()


# ─── Hydra Projector ──────────────────────────────────────────────────

@app.post("/v1/projectors/hydra/rebuild")
def rebuild_hydra():
    """Delete Hydra graph and rebuild from ledger."""
    from lab.ledger import Ledger
    from lab.projection import HydraProjector
    ledger = Ledger()
    projector = HydraProjector(ledger)
    return projector.rebuild()


@app.get("/v1/projectors/hydra/verify")
def verify_hydra():
    """Verify Hydra graph matches ledger state."""
    from lab.ledger import Ledger
    from lab.projection import HydraProjector
    ledger = Ledger()
    projector = HydraProjector(ledger)
    return projector.verify()


# ─── Pools & Matching ────────────────────────────────────────────────

@app.post("/v1/match")
def match_opportunity(demand: CapabilityDemand):
    """Match a capability demand to relevant pools."""
    pool_matches = match_demand_to_pools(demand)
    return {"pool_matches": [m.model_dump() for m in pool_matches]}


@app.post("/v1/context")
def get_context(req: ContextRequest):
    """Compile a context pack from specified pools."""
    from lab.modules import PoolMatch
    pool_matches = [PoolMatch(pool_id=pid, relevance=1.0, evidence_strength=0.5, transfer_prior=0.0)
                    for pid in req.pool_ids]
    context = compile_context(pool_matches, CapabilityDemand(), total_tokens=req.total_tokens)
    return context


@app.post("/v1/allocate")
def allocate(opportunity_id: str, module_id: str = "", worker_id: str = "", budget_usd: float = 0.0):
    """Make an allocation decision."""
    decision = controller.allocate(opportunity_id, module_id, worker_id, budget_usd)
    return decision.model_dump()


@app.post("/v1/dispatch")
def dispatch(decision_id: str, opportunity_id: str, module_id: str = ""):
    """Dispatch work to a module."""
    from lab.modules import AllocationDecision
    decision = AllocationDecision(
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        module_id=module_id,
    )
    assignment = controller.dispatch(decision)
    return assignment


@app.get("/v1/pools")
def list_pools():
    """List all capability pools."""
    from lab.pools.matcher import POOL_CENTROIDS
    return {"pools": list(POOL_CENTROIDS.keys())}


@app.get("/v1/pools/{pool_id}/stats")
def pool_stats(pool_id: str):
    """Get stats for a pool from HydraDB."""
    from integrations.hydra import get_pool_stats
    return get_pool_stats(pool_id)


@app.get("/v1/scientist/analyze/{pool_id}")
def analyze_pool(pool_id: str):
    """Analyze a pool's performance (Lab Scientist)."""
    from lab.scientist import LabScientist
    scientist = LabScientist()
    return scientist.analyze_pool_performance(pool_id)
