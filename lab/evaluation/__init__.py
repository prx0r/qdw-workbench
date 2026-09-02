"""Evaluation — reconstruction fidelity scoring + multi-dimensional metrics.

Per the CG bundle, a run must NOT be collapsed into one success scalar.
At minimum record:
    - authoritative benchmark task score
    - reconstruction fidelity against hidden state
    - calibration of worker confidence
    - information efficiency (observations/tool calls required)
    - planning efficiency (local experiments before action)
    - transfer to related held-out worlds
    - reproducibility under replay
    - cost and latency
    - invalid-action / false-positive rate

This module provides the scoring decomposition.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.contracts import EvaluationResult


@dataclass(frozen=True)
class ReconstructionScore:
    """How well the worker reconstructed the hidden state of the world."""
    fidelity: float = 0.0          # 0-1: fraction of hidden state correctly inferred
    completeness: float = 0.0      # 0-1: fraction of hidden variables discovered
    precision: float = 0.0         # 0-1: fraction of inferences that were correct
    false_positives: int = 0       # incorrect inferences
    false_negatives: int = 0       # missed hidden variables
    information_gathered: int = 0  # observations/tool calls used
    planning_experiments: int = 0  # internal simulations before acting

    @property
    def score(self) -> float:
        """Combined reconstruction fidelity score."""
        if self.completeness + self.precision == 0:
            return 0.0
        f1 = 2 * self.precision * self.completeness / (self.precision + self.completeness)
        return f1 * self.fidelity


@dataclass(frozen=True)
class CalibrationScore:
    """How well the worker's confidence matches actual correctness."""
    mean_confidence: float = 0.0
    actual_accuracy: float = 0.0
    brier_score: float = 0.0       # lower is better
    overconfident_rate: float = 0.0  # fraction where confidence > accuracy
    underconfident_rate: float = 0.0


@dataclass(frozen=True)
class EfficiencyScore:
    """Resource efficiency of the run."""
    observations_used: int = 0
    observations_optimal: int = 0   # minimum needed for perfect reconstruction
    tool_calls: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    wall_time_ms: int = 0
    invalid_actions: int = 0

    @property
    def information_efficiency(self) -> float:
        """How efficiently the worker gathered information."""
        if self.observations_optimal == 0:
            return 1.0
        return min(1.0, self.observations_optimal / max(1, self.observations_used))


@dataclass(frozen=True)
class RunMetrics:
    """Complete multi-dimensional metrics for a single run."""
    run_id: str
    worker_version_id: str
    world_id: str

    # Task completion
    task_score: float = 0.0
    task_success: bool = False

    # Reconstruction (separate from task)
    reconstruction: ReconstructionScore = field(default_factory=ReconstructionScore)

    # Calibration
    calibration: CalibrationScore = field(default_factory=CalibrationScore)

    # Efficiency
    efficiency: EfficiencyScore = field(default_factory=EfficiencyScore)

    # Transfer (filled in later when evaluated on held-out worlds)
    transfer_scores: dict[str, float] = field(default_factory=dict)

    # Reproducibility (filled in after replay)
    replay_consistent: bool | None = None
    replay_score_delta: float = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "worker_version_id": self.worker_version_id,
            "world_id": self.world_id,
            "task_score": self.task_score,
            "task_success": self.task_success,
            "reconstruction_fidelity": self.reconstruction.score,
            "reconstruction_completeness": self.reconstruction.completeness,
            "reconstruction_precision": self.reconstruction.precision,
            "information_efficiency": self.efficiency.information_efficiency,
            "tool_calls": self.efficiency.tool_calls,
            "tokens": self.efficiency.tokens_used,
            "cost_usd": self.efficiency.cost_usd,
            "invalid_actions": self.efficiency.invalid_actions,
            "brier_score": self.calibration.brier_score,
            "mean_confidence": self.calibration.mean_confidence,
            "transfer_scores": self.transfer_scores,
            "replay_consistent": self.replay_consistent,
        }


class RunEvaluator:
    """Evaluates a completed run across all dimensions."""

    def evaluate(
        self,
        run_id: str,
        worker_version_id: str,
        world_id: str,
        # Task
        task_score: float = 0.0,
        task_success: bool = False,
        # Hidden state (evaluator-only, never sent to worker)
        hidden_state: dict | None = None,
        worker_inferences: dict | None = None,
        # Efficiency
        observations_used: int = 0,
        observations_optimal: int = 0,
        tool_calls: int = 0,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        wall_time_ms: int = 0,
        invalid_actions: int = 0,
        # Confidence
        worker_confidence: float = 0.0,
    ) -> RunMetrics:
        """Evaluate a run across all dimensions."""

        # Reconstruction fidelity
        reconstruction = self._score_reconstruction(
            hidden_state or {}, worker_inferences or {}
        )

        # Calibration
        calibration = self._score_calibration(
            worker_confidence, task_score
        )

        # Efficiency
        efficiency = EfficiencyScore(
            observations_used=observations_used,
            observations_optimal=observations_optimal,
            tool_calls=tool_calls,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            wall_time_ms=wall_time_ms,
            invalid_actions=invalid_actions,
        )

        return RunMetrics(
            run_id=run_id,
            worker_version_id=worker_version_id,
            world_id=world_id,
            task_score=task_score,
            task_success=task_success,
            reconstruction=reconstruction,
            calibration=calibration,
            efficiency=efficiency,
        )

    def _score_reconstruction(
        self, hidden_state: dict, worker_inferences: dict
    ) -> ReconstructionScore:
        """Score how well the worker reconstructed hidden state."""
        if not hidden_state:
            return ReconstructionScore()

        correct = 0
        total_hidden = len(hidden_state)
        total_inferred = len(worker_inferences)

        for key, true_value in hidden_state.items():
            if key in worker_inferences:
                inferred = worker_inferences[key]
                # Compare (handles different types)
                if str(inferred).lower() == str(true_value).lower():
                    correct += 1

        false_positives = max(0, total_inferred - correct)
        false_negatives = max(0, total_hidden - correct)

        precision = correct / max(1, total_inferred)
        completeness = correct / max(1, total_hidden)
        fidelity = correct / max(1, total_hidden)

        return ReconstructionScore(
            fidelity=fidelity,
            completeness=completeness,
            precision=precision,
            false_positives=false_positives,
            false_negatives=false_negatives,
        )

    def _score_calibration(
        self, confidence: float, accuracy: float
    ) -> CalibrationScore:
        """Score calibration (confidence vs actual accuracy)."""
        brier = (confidence - accuracy) ** 2
        overconfident = 1.0 if confidence > accuracy else 0.0
        underconfident = 1.0 if confidence < accuracy - 0.2 else 0.0

        return CalibrationScore(
            mean_confidence=confidence,
            actual_accuracy=accuracy,
            brier_score=brier,
            overconfident_rate=overconfident,
            underconfident_rate=underconfident,
        )

    def to_evaluation_result(self, metrics: RunMetrics) -> EvaluationResult:
        """Convert RunMetrics to the standard EvaluationResult contract."""
        return EvaluationResult(
            result_id=f"eval-{metrics.run_id}",
            run_id=metrics.run_id,
            spec_id="multi-dimensional",
            success=metrics.task_success,
            scores=metrics.to_dict(),
            gates_passed=1 if metrics.task_success else 0,
            gates_total=1,
            overall_score=metrics.task_score,
        )
