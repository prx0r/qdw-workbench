"""Module status API — HTTP endpoints for modules to report to Private Lab.

This is the contract interface. Modules call these endpoints to report
their status, and Private Lab uses the responses to make allocation decisions.
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

app = FastAPI(title="Private Lab API", version="0.1.0")
controller = LabController()
registry = ModuleRegistry()


@app.get("/v1/health")
def health():
    return {"status": "ok", "modules": len(registry.list_modules())}


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


@app.post("/v1/match")
def match_opportunity(demand: CapabilityDemand):
    """Match a capability demand to relevant pools."""
    pool_matches = match_demand_to_pools(demand)
    return {"pool_matches": [m.model_dump() for m in pool_matches]}


@app.post("/v1/context")
def get_context(pool_ids: list[str], total_tokens: int = 8000):
    """Compile a context pack from specified pools."""
    matches = [CapabilityDemand(demands={pid: 1.0}) for pid in pool_ids]
    # Convert to PoolMatch objects
    from lab.modules import PoolMatch
    pool_matches = [PoolMatch(pool_id=pid, relevance=1.0, evidence_strength=0.5, transfer_prior=0.0)
                    for pid in pool_ids]
    context = compile_context(pool_matches, CapabilityDemand(), total_tokens=total_tokens)
    return context


@app.post("/v1/allocate")
def allocate(opportunity_id: str, module_id: str = "", worker_id: str = "", budget_usd: float = 0.0):
    """Make an allocation decision."""
    decision = controller.allocate(opportunity_id, module_id, worker_id, budget_usd)
    return decision.model_dump()


@app.post("/v1/dispatch")
def dispatch(decision_id: str, opportunity_id: str, module_id: str = ""):
    """Dispatch work to a module."""
    from lab.modules import AllocationDecision, PoolMatch
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
