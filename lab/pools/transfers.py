"""Pool transfer detection — find findings that cross venues.

Transfer evidence is the strongest proof that pool knowledge works.
A finding that improves performance in a different venue is a TRANSFER_CLAIM.
"""
from __future__ import annotations
from typing import Any
from integrations.hydra import get_client


def detect_transfers(pool_id: str | None = None) -> list[dict]:
    """Find findings that have been transferred across venues.

    A transfer is when a finding from one venue is applied in another venue
    and improves performance.
    """
    client = get_client()

    if pool_id:
        # Transfers within a specific pool
        results = client.run(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE' "
            "RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence, "
            "f.valid_in AS valid_in, f.transferred_to AS transferred_to, "
            "pool.name AS pool",
            pool=pool_id
        )
    else:
        # All transfers across all pools
        results = client.run(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
            "WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE' "
            "RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence, "
            "f.valid_in AS valid_in, f.transferred_to AS transferred_to, "
            "pool.name AS pool"
        )

    return results


def detect_cross_pool_transfers() -> list[dict]:
    """Find findings that transfer knowledge between different pools."""
    client = get_client()
    # HydraDB doesn't support WITH aggregation, so get all findings and filter in Python
    all_findings = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence, "
        "pool.name AS pool"
    )
    # Group by claim and find claims in multiple pools
    by_claim: dict[str, list[dict]] = {}
    for r in all_findings:
        claim = r["claim"]
        if claim not in by_claim:
            by_claim[claim] = []
        by_claim[claim].append(r)
    return [{"claim": c, "pools": list(set(r["pool"] for r in records)),
             "tier": records[0]["tier"]}
            for c, records in by_claim.items() if len(set(r["pool"] for r in records)) > 1]


def get_transfer_stats() -> dict:
    """Get overall transfer statistics."""
    client = get_client()

    # Count transfers by tier
    tier_counts = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "RETURN f.tier AS tier, f.claim AS claim, pool.name AS pool"
    )

    # Aggregate in Python
    tier_agg: dict[str, int] = {}
    claims_by_pool: dict[str, set] = {}
    for r in tier_counts:
        tier = r["tier"]
        tier_agg[tier] = tier_agg.get(tier, 0) + 1
        claim = r["claim"]
        if claim not in claims_by_pool:
            claims_by_pool[claim] = set()
        claims_by_pool[claim].add(r["pool"])

    cross_pool = sum(1 for pools in claims_by_pool.values() if len(pools) > 1)
    total = len(claims_by_pool)

    return {
        "total_findings": total,
        "transfers_by_tier": tier_agg,
        "cross_pool_transfers": cross_pool,
        "transfer_rate": cross_pool / max(1, total),
    }


def get_pool_transfer_matrix() -> dict:
    """Get a matrix of which pools transfer knowledge to which other pools."""
    client = get_client()

    # This requires findings that exist in multiple pools
    # For now, use a simplified approach
    pools = ["security", "smart-contract-security", "software-engineering",
             "forecasting", "research", "ai-redteam"]

    matrix = {}
    for pool in pools:
        findings = client.run(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE' "
            "RETURN f.claim AS claim",
            pool=pool
        )
        matrix[pool] = len(findings)

    return matrix
