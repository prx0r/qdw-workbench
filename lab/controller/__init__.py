"""Controller — orchestrate the lab loop.

The controller runs:
    INGEST → PROFILE → MATCH → VALUE → ALLOCATE → DISPATCH → OUTCOME → LEARN

It coordinates between modules, pools, Oracle, and HydraDB.
"""
from __future__ import annotations
import json
import time
from typing import Any
from lab.modules import (
    ModuleStatus, ModuleProgram, CapabilityDemand,
    PoolMatch, OpportunityMatch, AllocationDecision,
)
from lab.modules.registry import ModuleRegistry
from lab.pools.matcher import match_demand_to_pools
from lab.context.compiler import compile_context
from integrations.hydra import (
    get_client, hash_id,
    create_run_at_venue,
)


class LabController:
    """The brain of Private Lab.

    Orchestrates: ingest → match → allocate → dispatch → outcome → learn
    """

    def __init__(self):
        self.registry = ModuleRegistry()
        self.hydra = get_client()

    def ingest_module_status(self, status: ModuleStatus):
        """Receive a module status report."""
        self.registry.register_module(status)
        for prog in status.programs:
            self._project_program(status.module_id, prog)

    def ingest_opportunity(self, opportunity: dict) -> OpportunityMatch:
        """Receive an opportunity from MarketOracle and match it."""
        demand = CapabilityDemand(
            demands=opportunity.get("capability_demand", {})
        )
        pool_matches = match_demand_to_pools(demand)
        candidate_workers = []
        for match in pool_matches:
            workers = self._get_pool_workers(match.pool_id)
            candidate_workers.extend(workers)
        estimated_success = self._estimate_success(pool_matches, demand)
        match = OpportunityMatch(
            opportunity_id=opportunity.get("id", ""),
            capability_demand=demand,
            pool_matches=pool_matches,
            candidate_workers=candidate_workers[:5],
            estimated_success=estimated_success,
            estimated_cost_usd=opportunity.get("reward", 0) * 0.1,
            estimated_reward=opportunity.get("reward", 0),
            source=opportunity.get("src", "unknown"),
        )
        self._record_opportunity_match(match)
        return match

    def match_program_to_pools(self, module_id: str, program_id: str) -> list[PoolMatch]:
        """Match a module program to relevant pools."""
        status = self.registry.get_module(module_id)
        if not status:
            return []
        for prog in status.programs:
            if prog.program_id == program_id:
                demand = CapabilityDemand(demands=prog.capability_demand)
                return match_demand_to_pools(demand)
        return []

    def allocate(self, opportunity_id: str, module_id: str = "",
                 worker_id: str = "", budget_usd: float = 0.0) -> AllocationDecision:
        """Make an allocation decision."""
        decision_id = f"alloc-{int(time.time())}-{hash_id(opportunity_id) % 10000}"
        pool_matches = []
        if module_id:
            pool_matches = self.match_program_to_pools(module_id, opportunity_id)
        action = self._determine_action(pool_matches, budget_usd)
        decision = AllocationDecision(
            decision_id=decision_id,
            opportunity_id=opportunity_id,
            module_id=module_id,
            worker_id=worker_id,
            selected_pools=pool_matches,
            action=action,
            reason=self._allocation_reason(pool_matches, action),
            cost_usd=budget_usd,
        )
        self._record_allocation(decision)
        return decision

    def dispatch(self, decision: AllocationDecision) -> dict:
        """Dispatch work to a module via real ExecutionBackend."""
        from lab.execution import DirectBackend
        from lab.ledger import Ledger
        from lab.artifacts import ArtifactStore
        from lab.contracts import RunSpec, BudgetEnvelope, Split

        context = compile_context(
            pool_matches=decision.selected_pools,
            demand=CapabilityDemand(),
            total_tokens=8000,
        )

        # Build RunSpec
        run_id = f"run-{decision.decision_id}"
        run_spec = RunSpec(
            run_id=run_id,
            lab_id="private-lab",
            studio_id=decision.module_id or "unknown",
            task_instance_id=decision.opportunity_id,
            split=Split.TRAIN,
            worker_id=decision.worker_id or "default-worker",
            worker_version_id=f"{decision.worker_id}/v0",
        )
        budget = BudgetEnvelope(
            envelope_id=f"budget-{decision.decision_id}",
            cash_usd=decision.cost_usd,
            wall_seconds=60,
        )

        # Execute via DirectBackend (safe, no external dependencies)
        ledger = Ledger()
        artifacts = ArtifactStore()
        backend = DirectBackend(ledger, artifacts)
        result = backend.execute(run_spec, budget, context)

        # Record to ledger
        self.ledger.append_event(
            event_type="run.created",
            entity_id=run_id,
            payload={
                "run_id": run_id,
                "decision_id": decision.decision_id,
                "opportunity_id": decision.opportunity_id,
                "module_id": decision.module_id,
                "worker_version": run_spec.worker_version_id,
                "outcome": "executed",
            },
        )

        return {
            "decision_id": decision.decision_id,
            "run_id": run_id,
            "opportunity_id": decision.opportunity_id,
            "module_id": decision.module_id,
            "worker_version": run_spec.worker_version_id,
            "context_pack": context,
            "action": decision.action,
            "budget_usd": decision.cost_usd,
            "execution": {
                "success": result["success"],
                "artifacts": [a.artifact_id for a in result["artifacts"]],
                "duration_ms": result["duration_ms"],
            },
        }

    def record_outcome(self, decision_id: str, outcome: dict):
        """Record the outcome of a dispatched decision."""
        run_id = outcome.get("run_id", f"run-{decision_id}")
        create_run_at_venue(
            run_id=run_id,
            outcome=outcome.get("outcome", "pending"),
            venue_id=outcome.get("venue_id", "unknown"),
            venue_name=outcome.get("venue_name", "unknown"),
            pool_id=outcome.get("pool_id", "security"),
            pool_name=outcome.get("pool_name", "security"),
            **outcome,
        )

    def _project_program(self, module_id: str, prog: ModuleProgram):
        """Project a program to HydraDB graph."""
        pid = hash_id(prog.program_id)
        props = {"id": pid, "module": module_id, "name": prog.name, "state": prog.state}
        for k, v in prog.capability_demand.items():
            props[f"demand_{k}"] = v
        p_str = ", ".join(f"{k}: ${k}" for k in props)
        self.hydra.run_write(
            f"CREATE (p:Program {{{p_str}}})-[:_SELF]->(p2:Program {{id: $id}})", **props
        )
        self.hydra.run_write("MATCH (p:Program {id: $id})-[r:_SELF]->() DELETE r", id=pid)

    def _get_pool_workers(self, pool_id: str) -> list[str]:
        try:
            results = self.hydra.run(
                "MATCH (w:Worker)-[:MEMBER_OF]->(pool:CapabilityPool {name: $pool}) RETURN w.name AS name",
                pool=pool_id
            )
            return [r["name"] for r in results]
        except Exception:
            return []

    def _estimate_success(self, pool_matches: list[PoolMatch], demand: CapabilityDemand) -> float:
        if not pool_matches:
            return 0.1
        total_weight = sum(m.relevance for m in pool_matches)
        if total_weight == 0:
            return 0.1
        weighted_evidence = sum(m.evidence_strength * m.relevance for m in pool_matches)
        return min(0.95, weighted_evidence / total_weight * 0.8 + 0.1)

    def _determine_action(self, pool_matches: list[PoolMatch], budget: float) -> str:
        if not pool_matches:
            return "explore_new_worker"
        best = pool_matches[0]
        if best.evidence_strength > 0.7 and best.relevance > 0.7:
            return "submit_candidate"
        if best.evidence_strength > 0.4:
            return "train"
        return "explore_new_worker"

    def _allocation_reason(self, pool_matches: list[PoolMatch], action: str) -> str:
        if not pool_matches:
            return "No relevant pool evidence found, exploring new worker"
        best = pool_matches[0]
        return (f"Pool '{best.pool_id}' has relevance={best.relevance:.2f}, "
                f"evidence={best.evidence_strength:.2f}. Action: {action}")

    def _record_opportunity_match(self, match: OpportunityMatch):
        oid = hash_id(match.opportunity_id)
        props = {"id": oid, "opportunity_id": match.opportunity_id, "source": match.source,
                 "estimated_success": match.estimated_success}
        p_str = ", ".join(f"{k}: ${k}" for k in props)
        self.hydra.run_write(
            f"CREATE (o:OpportunityMatch {{{p_str}}})-[:_SELF]->(o2:OpportunityMatch {{id: $id}})", **props
        )
        self.hydra.run_write("MATCH (o:OpportunityMatch {id: $id})-[r:_SELF]->() DELETE r", id=oid)

    def _record_allocation(self, decision: AllocationDecision):
        did = hash_id(decision.decision_id)
        props = {"id": did, "decision_id": decision.decision_id, "opportunity_id": decision.opportunity_id,
                 "module_id": decision.module_id, "action": decision.action, "cost_usd": decision.cost_usd}
        p_str = ", ".join(f"{k}: ${k}" for k in props)
        self.hydra.run_write(
            f"CREATE (d:AllocationDecision {{{p_str}}})-[:_SELF]->(d2:AllocationDecision {{id: $id}})", **props
        )
        self.hydra.run_write("MATCH (d:AllocationDecision {id: $id})-[r:_SELF]->() DELETE r", id=did)
