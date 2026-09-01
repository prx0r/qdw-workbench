"""Budget allocator — cross-module capital allocation.

Inspired by Fleece's Thompson allocator and school league:
- Hierarchical shrinkage for cold start
- dTS discounting for non-stationarity
- Gini anti-concentration
- Immortal controls (baselines to beat)
"""
from __future__ import annotations
import math
from typing import Any
from lab.modules import ModuleProgram, PoolMatch
from lab.modules.registry import ModuleRegistry


# Immortal controls — baselines that evolution must beat
IMMORTAL_CONTROLS = [
    {"id": "ctrl-equal", "name": "Equal Allocation", "description": "Equal budget to all programs"},
    {"id": "ctrl-cheapest", "name": "Cheapest Model", "description": "Always use the cheapest available model"},
]


class BudgetAllocator:
    """Cross-module budget allocator.

    Uses Thompson-like sampling with hierarchical shrinkage:
    - Per-pool posterior from HydraDB evidence
    - Global fallback when pool evidence is sparse
    - dTS discounting for non-stationarity
    - Gini enforcement against concentration
    """

    def __init__(self, alpha0: float = 2.0, beta0: float = 2.0,
                 pool_weight: float = 0.7, explore_pct: float = 0.10):
        self.alpha0 = alpha0
        self.beta0 = beta0
        self.pool_weight = pool_weight  # blend: 70% pool-specific, 30% global
        self.explore_pct = explore_pct  # 10% for exploration

    def allocate(
        self,
        total_budget_usd: float,
        programs: list[tuple[str, ModuleProgram]],
        pool_matches: dict[str, list[PoolMatch]] | None = None,
    ) -> dict[str, float]:
        """Allocate budget across programs.

        Returns: {program_id: allocation_usd}
        """
        if not programs:
            return {}

        # Get pool-specific evidence
        pool_evidence = self._load_pool_evidence(programs)

        # Calculate base allocation per program
        allocations = {}
        for module_id, prog in programs:
            pid = prog.program_id

            # Get pool-specific posterior
            pool_posterior = self._get_pool_posterior(pid, pool_evidence)

            # Get global posterior (all programs in same pool)
            global_posterior = self._get_global_posterior(pid, pool_evidence)

            # Hierarchical shrinkage
            w = self.pool_weight
            alpha = self.alpha0 + w * pool_posterior["wins"] + (1 - w) * global_posterior["wins"]
            beta = self.beta0 + w * pool_posterior["losses"] + (1 - w) * global_posterior["losses"]

            # Thompson-like score (expected value of Beta distribution)
            score = alpha / (alpha + beta)

            # Apply PnL tilt if available
            tilt = self._pnl_tilt(pool_posterior.get("pnl", 0.0), pool_posterior.get("trades", 0))

            allocations[pid] = score * tilt

        # Normalize
        total_score = sum(allocations.values())
        if total_score > 0:
            for pid in allocations:
                allocations[pid] /= total_score

        # Apply exploration budget
        explore_budget = total_budget_usd * self.explore_pct
        exploit_budget = total_budget_usd * (1 - self.explore_pct)

        # Gini anti-concentration
        allocations = self._enforce_gini(allocations)

        # Convert to USD
        result = {}
        for pid, pct in allocations.items():
            result[pid] = pct * exploit_budget

        # Add exploration allocation to least-funded program
        if result:
            min_pid = min(result, key=result.get)
            result[min_pid] += explore_budget

        return result

    def _load_pool_evidence(self, programs: list[tuple[str, ModuleProgram]]) -> dict:
        """Load pool evidence from HydraDB."""
        # Placeholder — would query HydraDB for per-pool success counts
        return {}

    def _get_pool_posterior(self, program_id: str, evidence: dict) -> dict:
        """Get pool-specific posterior for a program."""
        # Placeholder — would query HydraDB for program-specific outcomes
        return {"wins": 0, "trades": 0, "losses": 0, "pnl": 0.0}

    def _get_global_posterior(self, program_id: str, evidence: dict) -> dict:
        """Get global posterior across all programs in same pool."""
        # Placeholder — would aggregate across pool
        return {"wins": 0, "trades": 0, "losses": 0, "pnl": 0.0}

    def _pnl_tilt(self, pnl: float, n: int) -> float:
        """PnL tilt — reward profitable programs."""
        if n == 0:
            return 1.0
        avg_pnl = pnl / n
        return max(0.05, 1.0 + 0.5 * math.tanh(avg_pnl * 2))

    def _enforce_gini(self, allocations: dict[str, float]) -> dict[str, float]:
        """Enforce Gini anti-concentration.

        If concentration (Gini) exceeds 0.5, flatten to uniform.
        """
        if len(allocations) <= 1:
            return allocations

        values = sorted(allocations.values())
        n = len(values)
        cumulative = 0.0
        gini_sum = 0.0
        for i, v in enumerate(values):
            cumulative += v
            gini_sum += (i + 1) * v
        gini = (2 * gini_sum) / (n * sum(values)) - (n + 1) / n if sum(values) > 0 else 0

        if gini > 0.5:
            # Flatten to uniform
            uniform = 1.0 / n
            return {k: uniform for k in allocations}

        return allocations
