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
    """Find findings that transfer knowledge between different pools.

    This is the strongest evidence of generalizable capability.
    """
    client = get_client()

    # Find findings that exist in multiple pools
    results = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "WITH f, collect(pool.name) AS pools "
        "WHERE size(pools) > 1 "
        "RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence, "
        "pools"
    )

    return results


def get_transfer_stats() -> dict:
    """Get overall transfer statistics."""
    client = get_client()

    # Count transfers by tier
    tier_counts = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE' "
        "RETURN f.tier AS tier, count(*) AS count"
    )

    # Count cross-pool transfers
    cross_pool = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "WITH f, collect(pool.name) AS pools "
        "WHERE size(pools) > 1 "
        "RETURN count(*) AS count"
    )

    # Count total findings
    total = client.run(
        "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool) "
        "RETURN count(*) AS count"
    )

    return {
        "total_findings": total[0]["count"] if total else 0,
        "transfers_by_tier": {r["tier"]: r["count"] for r in tier_counts},
        "cross_pool_transfers": cross_pool[0]["count"] if cross_pool else 0,
        "transfer_rate": (
            cross_pool[0]["count"] / max(1, total[0]["count"]) if total else 0
        ),
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
