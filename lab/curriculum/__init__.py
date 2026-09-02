"""Curriculum Engine — 6-level progression for security worlds.

Per the CG bundle:

Level 0 — known world, visible ground truth
Level 1 — known world, hidden state
Level 2 — randomized configuration within a known world family
Level 3 — new world assembled from known components
Level 4 — unseen architecture with only partial structural similarity
Level 5 — explicitly authorized external system where the local model is only an inferred approximation

The curriculum selects the next difficulty level based on the worker's
reconstruction fidelity, task performance, and calibration.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CurriculumLevel(IntEnum):
    """The 6 levels of the CG security curriculum."""
    KNOWN_VISIBLE = 0       # known world, visible ground truth
    KNOWN_HIDDEN = 1        # known world, hidden state
    RANDOMIZED = 2          # randomized config within known family
    ASSEMBLED = 3           # new world from known components
    UNSEEN_ARCH = 4         # unseen architecture, partial similarity
    AUTHORIZED_EXTERNAL = 5  # authorized external system, inferred model


@dataclass(frozen=True)
class WorldVariant:
    """A specific variant of a world for curriculum progression."""
    variant_id: str
    world_family: str
    level: CurriculumLevel
    difficulty: float = 0.0      # 0-1 within level
    seed: int = 0
    hidden_fraction: float = 0.0  # how much is hidden (0=visible, 1=fully hidden)
    config: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class CurriculumState:
    """Tracks curriculum progression for a worker."""
    worker_id: str
    current_level: CurriculumLevel = CurriculumLevel.KNOWN_VISIBLE
    level_scores: dict[str, list[float]] = field(default_factory=dict)
    experiments_completed: int = 0
    promotions: int = 0
    rejections: int = 0

    def record_result(self, level: str, score: float):
        if level not in self.level_scores:
            self.level_scores[level] = []
        self.level_scores[level].append(score)

    def level_mean(self, level: str) -> float:
        scores = self.level_scores.get(level, [])
        return sum(scores) / len(scores) if scores else 0.0

    def level_count(self, level: str) -> int:
        return len(self.level_scores.get(level, []))


class CurriculumEngine:
    """Selects next world variant based on worker performance.

    Progression rules:
    - Worker must complete N runs at current level
    - Mean reconstruction fidelity must exceed threshold
    - Mean task score must exceed threshold
    - Only then advance to next level
    """

    def __init__(
        self,
        runs_per_level: int = 5,
        fidelity_threshold: float = 0.6,
        task_threshold: float = 0.5,
        demote_on_regression: bool = True,
    ):
        self.runs_per_level = runs_per_level
        self.fidelity_threshold = fidelity_threshold
        self.task_threshold = task_threshold
        self.demote_on_regression = demote_on_regression

    def should_advance(self, state: CurriculumState) -> bool:
        """Check if worker should advance to next level."""
        level_name = state.current_level.name
        if state.level_count(level_name) < self.runs_per_level:
            return False

        mean_fidelity = state.level_mean(f"{level_name}_fidelity")
        mean_task = state.level_mean(level_name)

        return (
            mean_fidelity >= self.fidelity_threshold
            and mean_task >= self.task_threshold
        )

    def should_demote(self, state: CurriculumState) -> bool:
        """Check if worker should be demoted (regression detected)."""
        if not self.demote_on_regression:
            return False
        if state.current_level == CurriculumLevel.KNOWN_VISIBLE:
            return False

        level_name = state.current_level.name
        scores = state.level_scores.get(level_name, [])
        if len(scores) < 2:
            return False

        # Demote if last 2 runs are worse than first 2
        if len(scores) >= 4:
            first_half = sum(scores[:2]) / 2
            second_half = sum(scores[-2:]) / 2
            return second_half < first_half * 0.7

        return False

    def select_next(self, state: CurriculumState, variants: list[WorldVariant]) -> WorldVariant | None:
        """Select next variant based on curriculum state."""
        if not variants:
            return None

        # Filter to current level
        level_variants = [v for v in variants if v.level == state.current_level]

        # If should advance, try next level
        if self.should_advance(state):
            next_level = min(state.current_level + 1, CurriculumLevel.AUTHORIZED_EXTERNAL)
            next_variants = [v for v in variants if v.level == next_level]
            if next_variants:
                level_variants = next_variants

        # If should demote, go back one level
        if self.should_demote(state):
            prev_level = max(state.current_level - 1, CurriculumLevel.KNOWN_VISIBLE)
            prev_variants = [v for v in variants if v.level == prev_level]
            if prev_variants:
                level_variants = prev_variants

        if not level_variants:
            level_variants = variants

        # Select variant with best fit (closest to current difficulty)
        return min(level_variants, key=lambda v: abs(v.difficulty - 0.5))

    def record_run(
        self,
        state: CurriculumState,
        level: CurriculumLevel,
        reconstruction_fidelity: float,
        task_score: float,
    ) -> dict:
        """Record a run result and update curriculum state."""
        level_name = level.name
        state.record_result(level_name, task_score)
        state.record_result(f"{level_name}_fidelity", reconstruction_fidelity)
        state.experiments_completed += 1

        # Check advancement
        if self.should_advance(state):
            old_level = CurriculumLevel(state.current_level)
            next_val = min(state.current_level + 1, CurriculumLevel.AUTHORIZED_EXTERNAL)
            state.current_level = CurriculumLevel(next_val)
            return {
                "action": "advance",
                "from": old_level.name,
                "to": state.current_level.name,
                "mean_fidelity": state.level_mean(f"{level_name}_fidelity"),
                "mean_task": state.level_mean(level_name),
            }

        # Check demotion
        if self.should_demote(state):
            old_level = CurriculumLevel(state.current_level)
            prev_val = max(state.current_level - 1, CurriculumLevel.KNOWN_VISIBLE)
            state.current_level = CurriculumLevel(prev_val)
            return {
                "action": "demote",
                "from": old_level.name,
                "to": state.current_level.name,
            }

        return {
            "action": "continue",
            "level": level_name,
            "runs": state.level_count(level_name),
            "needed": self.runs_per_level,
        }

    def generate_worldpack_config(self, level: CurriculumLevel) -> dict:
        """Generate WorldPack config for a curriculum level."""
        configs = {
            CurriculumLevel.KNOWN_VISIBLE: {
                "hidden_fraction": 0.0,
                "reset_deterministic": True,
                "evaluator_visible": True,
                "variant_count": 1,
            },
            CurriculumLevel.KNOWN_HIDDEN: {
                "hidden_fraction": 0.5,
                "reset_deterministic": True,
                "evaluator_visible": False,
                "variant_count": 3,
            },
            CurriculumLevel.RANDOMIZED: {
                "hidden_fraction": 0.7,
                "reset_deterministic": False,
                "evaluator_visible": False,
                "variant_count": 10,
                "randomize_config": True,
            },
            CurriculumLevel.ASSEMBLED: {
                "hidden_fraction": 0.8,
                "reset_deterministic": False,
                "evaluator_visible": False,
                "variant_count": 20,
                "compose_from_components": True,
            },
            CurriculumLevel.UNSEEN_ARCH: {
                "hidden_fraction": 0.9,
                "reset_deterministic": False,
                "evaluator_visible": False,
                "variant_count": 5,
                "unseen_architecture": True,
            },
            CurriculumLevel.AUTHORIZED_EXTERNAL: {
                "hidden_fraction": 1.0,
                "reset_deterministic": False,
                "evaluator_visible": False,
                "variant_count": 1,
                "authorized_target": True,
            },
        }
        return configs.get(level, configs[CurriculumLevel.KNOWN_VISIBLE])
