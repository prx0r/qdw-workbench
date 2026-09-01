"""Experiment Lifecycle — CG/CGE boundaries + promotion gates.

Clear separation of concerns:

CGE / Lab Scientist may:
    - read TRAIN failures
    - read DEV failures
    - read Hydra patterns
    - identify failure clusters
    - propose candidate mutations
    - propose curriculum
    - generate LearningProposal

CGE may NOT:
    - see SECRET labels
    - declare candidate successful
    - promote WorkerVersion

CG owns:
    - sealed experiment
    - control/candidate comparison
    - paired tasks
    - quality gates
    - statistics
    - ExperimentResult
    - promotion evidence

Flow:
    RunReceipts → FailureCluster → LearningProposal → Candidate WorkerVersion
        → ExperimentSpec → CG → ExperimentResult → REJECT / PROMOTE

Only CG produces ExperimentResult. Only ExperimentResult can trigger promotion.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.contracts import (
    ExperimentSpec, ExperimentResult, ExperimentStatus,
    LearningProposal, Split, PromotionReceipt,
)
from lab.ledger import Ledger
from lab.artifacts import ArtifactStore
from lab.workers import WorkerRegistry


class ExperimentLifecycle:
    """Manages experiments with strict CG/CGE boundaries."""

    def __init__(self, ledger: Ledger, artifacts: ArtifactStore,
                 registry: WorkerRegistry):
        self.ledger = ledger
        self.artifacts = artifacts
        self.registry = registry

    # ─── CGE: Propose (may not see SECRET) ───────────────────────────

    def propose_experiment(
        self,
        hypothesis: str,
        control_version: str,
        candidate_version: str,
        task_family: str = "",
        n_tasks: int = 10,
        metrics: list[str] | None = None,
        promotion_rule: str = "",
    ) -> ExperimentSpec:
        """CGE proposes an experiment. Cannot see SECRET tasks."""
        # Extract worker_id from version_id (e.g., "security-01/v0" → "security-01")
        worker_id = control_version.rsplit("/", 1)[0] if "/" in control_version else ""

        spec = ExperimentSpec(
            experiment_id=f"exp-{worker_id}-{int(datetime.now(timezone.utc).timestamp())}",
            hypothesis=hypothesis,
            control_worker_version=control_version,
            candidate_worker_version=candidate_version,
            task_family=task_family,
            split=Split.DEV,  # CGE never sees SECRET
            n_tasks=n_tasks,
            metrics=metrics or ["quality", "cost", "duration"],
            promotion_rule=promotion_rule,
        )

        # Record to ledger
        self.ledger.append_event(
            event_type="experiment.created",
            entity_id=spec.experiment_id,
            payload={
                "experiment_id": spec.experiment_id,
                "hypothesis": hypothesis,
                "control_version": control_version,
                "candidate_version": candidate_version,
                "task_family": task_family,
                "n_tasks": n_tasks,
                "metrics": spec.metrics,
            },
        )

        # Store spec as artifact
        self.artifacts.store_json(
            spec.model_dump(), name=f"experiment-{spec.experiment_id}.json"
        )

        return spec

    # ─── CG: Seal experiment (no more changes) ────────────────────────

    def seal_experiment(self, experiment_id: str) -> dict:
        """CG seals the experiment — no more mutations allowed."""
        self.ledger.append_event(
            event_type="experiment.sealed",
            entity_id=experiment_id,
            payload={"experiment_id": experiment_id, "sealed_at": datetime.now(timezone.utc).isoformat()},
        )
        return {"experiment_id": experiment_id, "status": "sealed"}

    # ─── CG: Evaluate (only CG produces ExperimentResult) ─────────────

    def evaluate(
        self,
        experiment_id: str,
        control_quality: float,
        candidate_quality: float,
        control_cost: float = 0.0,
        candidate_cost: float = 0.0,
        confidence_interval: tuple[float, float] = (0.0, 0.0),
        regressions: list[str] | None = None,
        reason: str = "",
    ) -> ExperimentResult:
        """CG evaluates the experiment. Only CG produces ExperimentResult."""
        quality_delta = candidate_quality - control_quality
        cost_delta = candidate_cost - control_cost

        # Determine promotion based on quality delta and confidence
        promoted = (
            quality_delta > 0
            and abs(confidence_interval[0]) < abs(quality_delta)
        )

        result = ExperimentResult(
            result_id=f"result-{experiment_id}",
            experiment_id=experiment_id,
            control_quality=control_quality,
            candidate_quality=candidate_quality,
            quality_delta=quality_delta,
            confidence_interval=confidence_interval,
            control_cost=control_cost,
            candidate_cost=candidate_cost,
            cost_delta=cost_delta,
            regressions=regressions or [],
            promoted=promoted,
            reason=reason,
        )

        # Record to ledger
        self.ledger.append_event(
            event_type="experiment.evaluated",
            entity_id=experiment_id,
            payload={
                "experiment_id": experiment_id,
                "result_id": result.result_id,
                "control_quality": control_quality,
                "candidate_quality": candidate_quality,
                "quality_delta": quality_delta,
                "promoted": promoted,
                "reason": reason,
            },
        )

        # Store result as artifact
        self.artifacts.store_json(
            result.model_dump(), name=f"result-{experiment_id}.json"
        )

        return result

    # ─── CG: Promote or Reject ────────────────────────────────────────

    def promote(
        self,
        experiment_result: ExperimentResult,
        reason: str = "",
    ) -> PromotionReceipt | None:
        """CG promotes a candidate. Only possible if ExperimentResult.promoted=True."""
        if not experiment_result.promoted:
            return None

        # Extract candidate version from experiment
        # Look up the experiment to get candidate_version
        events = self.ledger.get_entity_history(experiment_result.experiment_id)
        exp_events = [e for e in events if e["event_type"] == "experiment.created"]
        if not exp_events:
            return None

        payload = json.loads(exp_events[0]["payload_json"])
        candidate_version = payload.get("candidate_version", "")
        worker_id = candidate_version.rsplit("/", 1)[0] if "/" in candidate_version else ""

        # Create promotion receipt
        receipt = self.registry.promote(
            worker_id=worker_id,
            candidate_version=candidate_version,
            experiment_result_id=experiment_result.result_id,
            reason=reason or experiment_result.reason,
        )

        return receipt

    def reject(self, experiment_result: ExperimentResult, reason: str = "") -> dict:
        """CG rejects a candidate."""
        self.ledger.append_event(
            event_type="experiment.rejected",
            entity_id=experiment_result.experiment_id,
            payload={
                "experiment_id": experiment_result.experiment_id,
                "reason": reason or experiment_result.reason,
            },
        )
        return {
            "experiment_id": experiment_result.experiment_id,
            "status": "rejected",
            "reason": reason or experiment_result.reason,
        }

    # ─── Queries ──────────────────────────────────────────────────────

    def get_experiment_history(self, experiment_id: str) -> list[dict]:
        """Get all events for an experiment."""
        return self.ledger.get_entity_history(experiment_id)

    def get_pending_experiments(self) -> list[dict]:
        """Get experiments that haven't been evaluated yet."""
        events = self.ledger.get_events_by_type("experiment.created", limit=100)
        evaluated = set()
        for e in self.ledger.get_events_by_type("experiment.evaluated", limit=100):
            evaluated.add(e["entity_id"])

        pending = []
        for e in events:
            if e["entity_id"] not in evaluated:
                payload = json.loads(e["payload_json"])
                pending.append(payload)
        return pending
