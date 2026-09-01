"""Pool matcher — match capabilities to relevant pools.

Pools are queryable views over the Lab graph.
A pool contains shared doctrine, findings, skills, and evaluators.
Matching uses capability demand vectors against pool centroids.
"""
from __future__ import annotations
from typing import Any
from lab.modules import CapabilityDemand, PoolMatch
from integrations.hydra import get_client, hash_id


# Pool centroids — what each pool is strong at
POOL_CENTROIDS: dict[str, dict[str, float]] = {
    "security": {
        "security": 1.0, "smart_contract": 0.9, "solidity": 0.85,
        "vulnerability_detection": 0.95, "code_audit": 0.9,
        "exploit_reasoning": 0.8, "report_writing": 0.7,
        "fuzzing": 0.6, "access_control": 0.85, "reentrancy": 0.8,
    },
    "smart-contract-security": {
        "security": 0.9, "smart_contract": 1.0, "solidity": 0.95,
        "vyper": 0.7, "cairo": 0.5, "move": 0.4,
        "vulnerability_detection": 0.9, "reentrancy": 0.95,
        "access_control": 0.9, "flash_loan": 0.8, "oracle_manipulation": 0.7,
    },
    "software-engineering": {
        "software_engineering": 1.0, "api_development": 0.85,
        "web_apps": 0.8, "cli_tools": 0.7, "testing": 0.8,
        "python": 0.8, "javascript": 0.8, "rust": 0.6, "go": 0.5,
    },
    "forecasting": {
        "forecasting": 1.0, "probability": 0.9, "calibration": 0.85,
        "evidence_gathering": 0.8, "base_rate": 0.7, "uncertainty": 0.8,
    },
    "research": {
        "research": 1.0, "web_search": 0.9, "analysis": 0.85,
        "synthesis": 0.8, "report_writing": 0.75, "fact_checking": 0.7,
    },
    "ai-redteam": {
        "security": 0.8, "ai_security": 1.0, "prompt_injection": 0.9,
        "rag_poisoning": 0.85, "agent_exploitation": 0.9, "llm": 0.8,
        "adversarial": 0.85, "tool_abuse": 0.8,
    },
}


def match_demand_to_pools(
    demand: CapabilityDemand,
    top_k: int = 3,
    min_relevance: float = 0.3,
) -> list[PoolMatch]:
    """Match a capability demand vector to relevant pools.

    Uses cosine-like similarity between demand vector and pool centroids.
    """
    matches = []
    demand_vec = demand.demands

    if not demand_vec:
        return matches

    for pool_id, centroid in POOL_CENTROIDS.items():
        # Calculate relevance: overlap between demand and centroid
        relevance = _calculate_relevance(demand_vec, centroid)
        if relevance < min_relevance:
            continue

        # Evidence strength: how many findings/skills does this pool have
        evidence_strength = _get_pool_evidence_strength(pool_id)

        # Transfer prior: how often has this pool transferred knowledge
        transfer_prior = _get_pool_transfer_prior(pool_id)

        # Reasons
        reasons = _get_match_reasons(demand_vec, centroid, pool_id)

        matches.append(PoolMatch(
            pool_id=pool_id,
            relevance=relevance,
            evidence_strength=evidence_strength,
            transfer_prior=transfer_prior,
            reasons=reasons,
        ))

    # Sort by relevance * evidence_strength
    matches.sort(key=lambda m: m.relevance * (0.5 + m.evidence_strength * 0.5), reverse=True)
    return matches[:top_k]


def _calculate_relevance(demand: dict[str, float], centroid: dict[str, float]) -> float:
    """Calculate relevance between demand and centroid vectors."""
    # Find overlapping keys
    demand_keys = set(demand.keys())
    centroid_keys = set(centroid.keys())
    overlap = demand_keys & centroid_keys

    if not overlap:
        # Check parent/child relationships
        return _check_hierarchical_match(demand, centroid)

    # Weighted average of overlapping capabilities
    total_weight = 0.0
    weighted_score = 0.0
    for key in overlap:
        weight = max(demand[key], centroid[key])  # higher of the two
        score = min(demand[key], centroid[key]) / max(demand[key], centroid[key], 0.01)
        total_weight += weight
        weighted_score += weight * score

    return weighted_score / total_weight if total_weight > 0 else 0.0


def _check_hierarchical_match(demand: dict[str, float], centroid: dict[str, float]) -> float:
    """Check for parent/child capability relationships."""
    # Simple hierarchy: security > smart_contract, software > api, etc.
    hierarchy = {
        "security": ["smart_contract", "ai_security", "adversarial"],
        "software_engineering": ["api_development", "web_apps", "cli_tools"],
        "smart_contract": ["solidity", "vyper", "cairo", "move"],
    }

    score = 0.0
    count = 0
    for parent, children in hierarchy.items():
        if parent in demand:
            for child in children:
                if child in centroid:
                    score += demand[parent] * centroid[child] * 0.5  # discount for indirect
                    count += 1
        if parent in centroid:
            for child in children:
                if child in demand:
                    score += centroid[parent] * demand[child] * 0.5
                    count += 1

    return score / count if count > 0 else 0.0


def _get_pool_evidence_strength(pool_id: str) -> float:
    """Get evidence strength from HydraDB pool findings."""
    try:
        client = get_client()
        result = client.run_one(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "RETURN count(*) AS count",
            pool=pool_id
        )
        count = result["count"] if result else 0
        # Normalize: 0 findings = 0.0, 50+ findings = 1.0
        return min(1.0, count / 50.0)
    except Exception:
        return 0.0


def _get_pool_transfer_prior(pool_id: str) -> float:
    """Get transfer prior from HydraDB transferred findings."""
    try:
        client = get_client()
        result = client.run_one(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE' "
            "RETURN count(*) AS count",
            pool=pool_id
        )
        count = result["count"] if result else 0
        return min(1.0, count / 10.0)
    except Exception:
        return 0.0


def _get_match_reasons(demand: dict[str, float], centroid: dict[str, float], pool_id: str) -> list[str]:
    """Generate human-readable reasons for the match."""
    reasons = []
    overlap = set(demand.keys()) & set(centroid.keys())
    for key in sorted(overlap, key=lambda k: demand[k] * centroid[k], reverse=True)[:3]:
        reasons.append(f"strong {key} match (demand={demand[key]:.2f}, pool={centroid[key]:.2f})")
    if not reasons:
        reasons.append(f"indirect capability match via {pool_id} hierarchy")
    return reasons
