"""Scientist — experiment proposals from evidence.

Reads: HydraDB findings, pool performance, budgets, graveyard
Proposes: experiments to try, pools to split/merge, skills to test
Never: declares itself correct
"""
from __future__ import annotations
from typing import Any
from integrations.hydra import get_client


class LabScientist:
    """Reads evidence, proposes experiments. Never judges."""

    def __init__(self):
        self.hydra = get_client()

    def analyze_pool_performance(self, pool_id: str) -> dict:
        """Analyze a pool's performance and identify improvement opportunities."""
        findings = self.hydra.run(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "RETURN f.tier AS tier, f.claim AS claim, f.confidence AS confidence",
            pool=pool_id
        )
        transfers = [f for f in findings if f.get("tier") in ("TRANSFER_CLAIM", "DOCTRINE")]
        failures = [f for f in findings if f.get("tier") == "OBSERVATION"]

        recommendations = []
        if len(failures) > 5 and len(transfers) < 2:
            recommendations.append("Many observations but few validated findings — run more controlled experiments")
        if len(transfers) == 0:
            recommendations.append("No transfer evidence yet — test findings in adjacent venues")
        if len(failures) > 3:
            recommendations.append("Multiple failure patterns — consider skill specialization")

        return {
            "pool": pool_id,
            "total_findings": len(findings),
            "transfers": len(transfers),
            "failures": len(failures),
            "recommendations": recommendations,
        }

    def propose_experiment(self, pool_id: str, hypothesis: str) -> dict:
        """Propose an experiment for a pool."""
        return {
            "type": "experiment_proposal",
            "pool_id": pool_id,
            "hypothesis": hypothesis,
            "status": "PROPOSED",
            "requires_evaluation": True,
        }
