"""Execution Backend — real execution through WorkerKit.

Current LabController.dispatch() is conceptually useful but is not yet execution.
It constructs a dict rather than actually running WorkerKit.

Introduce:
    class ExecutionBackend(Protocol):
        def execute(self, run_spec: RunSpec) -> ExecutionResult:
            ...

Then:
    WorkerKitBackend becomes the first real implementation.

Private Lab lifecycle must be:
    TaskInstance + WorkerVersion + ContextPack + BudgetEnvelope
        ↓
    RunSpec
        ↓
    ExecutionBackend
        ↓
    artifacts
        ↓
    Evaluator
        ↓
    EvaluationResult
        ↓
    RunReceipt

dispatch() must eventually invoke this.
Do not allow: return {"worker_version": "...", "action": "..."}
to count as execution.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Protocol, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.contracts import (
    RunSpec, RunReceipt, EvaluationResult, BudgetEnvelope,
    ArtifactRef, TrajectoryRef, Split, RunMode,
)
from lab.artifacts import ArtifactStore
from lab.ledger import Ledger


class ExecutionResult(Protocol):
    """Result of executing a run through a backend."""
    success: bool
    artifacts: list[ArtifactRef]
    trajectory: TrajectoryRef | None
    evaluation_result: EvaluationResult
    duration_ms: int
    cost_usd: float
    metadata: dict


class ExecutionBackend(Protocol):
    """Protocol for execution backends."""

    def execute(self, run_spec: RunSpec, budget: BudgetEnvelope,
                context: str = "") -> dict:
        """Execute a run. Returns dict with artifacts, evaluation, receipt."""
        ...


class WorkerKitBackend:
    """Real execution through WorkerKit / Letta runtime.

    Sends tasks to the Letta runtime service (localhost:3000).
    """
    RUNTIME_URL = "http://localhost:3000"
    WORKER_ID = "lab-worker-v1"

    def __init__(self, ledger: Ledger, artifacts: ArtifactStore):
        self.ledger = ledger
        self.artifacts = artifacts

    def execute(self, run_spec: RunSpec, budget: BudgetEnvelope,
                context: str = "") -> dict:
        """Execute a run through Letta runtime."""
        t0 = time.time()

        # Ensure worker exists
        self._letta_request("POST", "/workers", {
            "worker_id": self.WORKER_ID,
            "model": "opencode-go/mimo-v2.5",
            "persona": "You are a Moltwork lab worker. Complete tasks precisely.",
        })

        # Build task message
        task = f"Complete task: {run_spec.task_instance_id}"
        if context:
            task += f"\n\nContext:\n{context}"
        task += "\n\nReturn JSON: {\"status\": \"complete\", \"writes\": [{\"path\": \"file\", \"content\": \"data\"}], \"notes\": \"what you did\"}"

        # Execute
        timeout = min(budget.wall_seconds, 300) if budget.wall_seconds else 300
        result = self._letta_request("POST", f"/workers/{self.WORKER_ID}/run", {
            "task": task,
            "workspace": f"/tmp/lab-run-{run_spec.run_id}",
            "timeout": timeout,
            "genome": {"memory_mode": "letta", "max_steps": 4},
            "allowedTools": ["Read", "Write", "Edit", "LS", "Glob", "Grep"],
        }, timeout=timeout + 60)

        duration_ms = int((time.time() - t0) * 1000)
        output = result.get("output_content", "")
        ok = result.get("ok", bool(output))
        cost_usd = 0.0  # Free tier

        # Store trajectory as artifact
        traj_receipt = self.artifacts.store_json(
            {
                "run_id": run_spec.run_id,
                "output": output,
                "tool_calls": result.get("tool_calls", []),
                "agent_id": result.get("agent_id", ""),
            },
            name=f"trajectory-{run_spec.run_id}.json",
        )

        # Store output as artifact
        output_receipt = self.artifacts.store_text(
            output, name=f"output-{run_spec.run_id}.txt"
        )

        # Build artifact refs
        artifacts = [
            ArtifactRef(
                artifact_id=traj_receipt["digest"],
                name=traj_receipt["name"],
                media_type=traj_receipt["media_type"],
                sha256=traj_receipt["digest"],
                size_bytes=traj_receipt["size_bytes"],
            ),
            ArtifactRef(
                artifact_id=output_receipt["digest"],
                name=output_receipt["name"],
                media_type=output_receipt["media_type"],
                sha256=output_receipt["digest"],
                size_bytes=output_receipt["size_bytes"],
            ),
        ]

        # Build trajectory ref
        trajectory = TrajectoryRef(
            trajectory_id=f"traj-{run_spec.run_id}",
            run_id=run_spec.run_id,
            content_hash=traj_receipt["digest"],
            step_count=len(result.get("tool_calls", [])),
        )

        # Record execution event to ledger
        self.ledger.append_event(
            event_type="run.executed",
            entity_id=run_spec.run_id,
            payload={
                "run_id": run_spec.run_id,
                "worker_version": run_spec.worker_version_id,
                "success": ok,
                "duration_ms": duration_ms,
                "cost_usd": cost_usd,
                "artifacts": [a.artifact_id for a in artifacts],
                "trajectory_id": trajectory.trajectory_id,
            },
        )

        # Return execution result
        return {
            "success": ok,
            "artifacts": artifacts,
            "trajectory": trajectory,
            "duration_ms": duration_ms,
            "cost_usd": cost_usd,
            "output": output,
            "metadata": {
                "harness": "letta",
                "model": "mimo-v2.5",
                "agent_id": result.get("agent_id", ""),
                "tool_calls_count": len(result.get("tool_calls", [])),
            },
        }

    def _letta_request(self, method: str, path: str, data: dict = None,
                       timeout: int = 180) -> dict:
        url = f"{self.RUNTIME_URL}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e), "ok": False}


class DirectBackend:
    """Direct execution for testing (no external services needed)."""

    def __init__(self, ledger: Ledger, artifacts: ArtifactStore):
        self.ledger = ledger
        self.artifacts = artifacts

    def execute(self, run_spec: RunSpec, budget: BudgetEnvelope,
                context: str = "") -> dict:
        """Execute directly (for testing)."""
        # Store a synthetic output
        output = f"Direct execution of {run_spec.task_instance_id}"
        output_receipt = self.artifacts.store_text(
            output, name=f"output-{run_spec.run_id}.txt"
        )
        artifacts = [
            ArtifactRef(
                artifact_id=output_receipt["digest"],
                name=output_receipt["name"],
                media_type=output_receipt["media_type"],
                sha256=output_receipt["digest"],
                size_bytes=output_receipt["size_bytes"],
            ),
        ]

        # Record to ledger
        self.ledger.append_event(
            event_type="run.executed",
            entity_id=run_spec.run_id,
            payload={
                "run_id": run_spec.run_id,
                "worker_version": run_spec.worker_version_id,
                "success": True,
                "duration_ms": 0,
                "cost_usd": 0.0,
                "artifacts": [a.artifact_id for a in artifacts],
            },
        )

        return {
            "success": True,
            "artifacts": artifacts,
            "trajectory": None,
            "duration_ms": 0,
            "cost_usd": 0.0,
            "output": output,
            "metadata": {"harness": "direct"},
        }
