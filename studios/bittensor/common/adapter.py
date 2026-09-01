"""Bittensor Studio — domain adapter for Bittensor subnets.

From spec §20: Each subnet is a different environment.
Generic Bittensor package handles wallet, registration, economics.
Studio handles task semantics, local benchmark, evaluator, curriculum.
"""
from __future__ import annotations

from lab.contracts import (
    TaskInstance, Split, RunSpec, RunReceipt, EvaluationResult,
    StudioManifest, ExternalSubmissionReceipt, ExternalOutcomeReceipt,
)


class BittensorStudio:
    """Base adapter for Bittensor subnets."""

    def __init__(self, subnet_id: int, subnet_name: str):
        self.subnet_id = subnet_id
        self.subnet_name = subnet_name

    def manifest(self) -> StudioManifest:
        return StudioManifest(
            studio_id=f"bittensor/{self.subnet_id}",
            name=f"Bittensor {self.subnet_name} (SN{self.subnet_id})",
            task_families=[f"bittensor.{self.subnet_name}"],
            evaluator_versions=["emission-v1"],
            modes=["SHADOW", "LIVE"],
        )

    def get_task(self, split: Split, seed: int | None = None) -> TaskInstance:
        raise NotImplementedError("Subclass must implement get_task")

    def evaluate(self, run: RunReceipt, task: TaskInstance) -> EvaluationResult:
        raise NotImplementedError("Subclass must implement evaluate")

    def observe_external_outcome(self, submission_id: str) -> ExternalOutcomeReceipt | None:
        raise NotImplementedError("Subclass must implement observe_external_outcome")

    def curriculum_features(self, run: RunReceipt) -> dict:
        return {
            "studio": f"bittensor/{self.subnet_id}",
            "subnet_id": self.subnet_id,
        }


class DittoStudio(BittensorStudio):
    """SN118 — Ditto: distributed inference."""

    def __init__(self):
        super().__init__(118, "ditto")


class RidgesStudio(BittensorStudio):
    """SN62 — Ridges: coding agent."""

    def __init__(self):
        super().__init__(62, "ridges")
